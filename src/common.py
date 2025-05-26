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


def parse_bool_env(value) -> bool:
    """
    Parse boolean value from environment variable.
    Supports both string and boolean inputs for compatibility with different MCP clients.
    
    Args:
        value: Environment variable value (string, bool, or None)
        
    Returns:
        Boolean value
    """
    if value is None:
        return True  # Default to True for SSL
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        # Handle string representations
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    
    # Fallback to bool conversion
    return bool(value)


@dataclass
class Env:

    __namespace__ = 'ctera.mcp.core.settings'

    def __init__(self, scope, host, user, password):
        self.scope = scope
        self.host = host
        self.user = user
        self.password = password
        self.port = int(os.environ.get(f'{Env.__namespace__}.port', 443))
        
        # Handle SSL configuration with support for both string and boolean values
        # Check for connector.ssl setting first (matches claude_desktop_config.json)
        connector_ssl = os.environ.get(f'{Env.__namespace__}.connector.ssl', None)
        if connector_ssl is not None:
            self.ssl = parse_bool_env(connector_ssl)
        else:
            # Fallback to regular ssl setting
            self.ssl = parse_bool_env(os.environ.get(f'{Env.__namespace__}.ssl', True))

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
    """
    @functools.wraps(function)
    async def wrapper(*args, **kwargs):
        # Find context - check kwargs first, then args
        ctx = kwargs.get('ctx')
        if not ctx and args:
            ctx = next((arg for arg in args if hasattr(arg, 'request_context')), None)
        
        if not ctx:
            raise ValueError("Context not found in function arguments")
        
        portal_context = ctx.request_context.lifespan_context
        
        try:
            return await function(*args, **kwargs)
        except SessionExpired:
            logger.info("Session expired, refreshing...")
            await portal_context.login()  # Re-authenticate with stored credentials
            return await function(*args, **kwargs)  # Retry
        except Exception as e:
            logger.info(f"Exception occurred, attempting session refresh... ({e})")
            await portal_context.login()  # Re-authenticate with stored credentials
            return await function(*args, **kwargs)  # Retry

    return wrapper
