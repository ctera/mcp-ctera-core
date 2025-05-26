import os
import logging
import functools
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable
from mcp.server.fastmcp import FastMCP
from cterasdk import AsyncGlobalAdmin, AsyncServicesPortal, settings
from cterasdk.exceptions import SessionExpired


logger = logging.getLogger('ctera.mcp.core')
logger.info("Starting CTERA Portal Model Context Protocol [MCP] Server.")


@dataclass
class Env:

    __namespace__ = 'ctera.mcp.core.settings'

    def __init__(self, scope, host, user, password):
        self.scope = scope
        self.host = host
        self.user = user
        self.password = password
        self.port = os.environ.get(f'{Env.__namespace__}.port', 443)
        self.ssl = os.environ.get(f'{Env.__namespace__}.ssl', True)
        # Check for connector.ssl setting (matches mcp.json configuration)
        connector_ssl = os.environ.get(f'{Env.__namespace__}.connector.ssl', None)
        if connector_ssl is not None:
            # Convert string 'false'/'true' to boolean
            self.ssl = connector_ssl.lower() == 'true' if isinstance(connector_ssl, str) else bool(connector_ssl)

    @staticmethod
    def load():
        scope = os.environ.get(f'{Env.__namespace__}.scope', None)
        host = os.environ.get(f'{Env.__namespace__}.host', None)
        user = os.environ.get(f'{Env.__namespace__}.user', None)
        password = os.environ.get(f'{Env.__namespace__}.password', None)
        return Env(scope, host, user, password)


@dataclass
class PortalContext:

    def __init__(self, core, env: Env):
        settings.core.asyn.settings.connector.ssl = env.ssl
        self._session = core(env.host, env.port)
        self._user = env.user
        self._password = env.password

    @property
    def session(self):
        return self._session

    async def login(self):
        """
        Login.
        """
        await self.session.login(self._user, self._password)

    async def logout(self):
        """
        Logout.
        """
        await self.session.logout()

    @staticmethod  
    def initialize(env: Env):
        """
        Initialize Portal Context.
        """
        if env.scope == 'admin':
            return PortalContext(AsyncGlobalAdmin, env)
        elif env.scope == 'user':
            return PortalContext(AsyncServicesPortal, env)
        else:
            raise ValueError(f'Scope error: value must be "admin" or "user": {env.scope}')


@asynccontextmanager
async def ctera_lifespan(mcp: FastMCP) -> AsyncIterator[PortalContext]:   
    env = Env.load()
    user = PortalContext.initialize(env)
    try:
        await user.login()
        yield user
    finally:
        await user.logout()


mcp = FastMCP("ctera-core-mcp-server", lifespan=ctera_lifespan)


def with_session_refresh(function: Callable) -> Callable:
    """
    Decorator to handle session expiration and automatic refresh.

    Args:
        function: The function to wrap with session refresh logic

    Returns:
        Wrapped function that handles session refresh
    """
    @functools.wraps(function)
    async def wrapper(*args, **kwargs):
        # Extract context from kwargs or args
        ctx = kwargs.get('ctx')
        if ctx is None:
            # Look for Context in args
            from mcp.server.fastmcp import Context
            for arg in args:
                if isinstance(arg, Context):
                    ctx = arg
                    break
        
        if ctx is None:
            raise ValueError("Context not found in function arguments")
        
        # Get the portal context which contains the session and credentials
        portal_context = ctx.request_context.lifespan_context
        if portal_context is None:
            raise Exception("Portal connection not available. Please check environment variables.")
        
        try:
            # Try the original function
            return await function(*args, **kwargs)
        except Exception as e:
            # Check if it's a session expired error (multiple ways to detect)
            error_msg = str(e).lower()
            is_session_error = (
                isinstance(e, SessionExpired) or
                "session expired" in error_msg or 
                "session invalid" in error_msg or
                "unauthorized" in error_msg or
                "authentication" in error_msg or
                "401" in error_msg
            )
            
            if is_session_error:
                logger.info(f"Session expired or authentication error detected: {e}")
                logger.info("Attempting to refresh session...")
                try:
                    # Re-authenticate using the stored credentials in portal_context
                    await portal_context.login()
                    logger.info("Session refreshed successfully, retrying operation...")
                    # Retry the function
                    return await function(*args, **kwargs)
                except Exception as refresh_error:
                    logger.error(f"Failed to refresh session: {refresh_error}")
                    raise Exception(f"Session refresh failed: {refresh_error}") from e
            else:
                # If it's another error, log and re-raise it
                logger.error(f'Uncaught exception in {function.__name__}: {e}')
                raise
    
    return wrapper
