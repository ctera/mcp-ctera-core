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

logger = logging.getLogger('cterasdk.core').setLevel(logging.DEBUG)


@dataclass
class Env:

    __namespace__ = 'ctera.mcp.core.settings'

    def __init__(self, scope, host, user, password):
        self.scope = scope
        self.host = host
        self.user = user
        self.password = password
        self.port = os.environ.get(f'{Env.__namespace__}.port', 443)
        ssl = os.environ.get(f'{Env.__namespace__}.ssl', None)
        self.ssl = False if ssl in ['false', False] else True

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
        ctx = kwargs.get('ctx')
        user = ctx.request_context.lifespan_context.session
        try:
            return await function(*args, **kwargs)
        except SessionExpired:
            await user.login()
            return await function(*args, **kwargs)
        except Exception as e:
            logger.error(f'Uncaught exception: {e}')

    return wrapper
