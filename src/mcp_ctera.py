import os
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator


from cterasdk import (
    AsyncServicesPortal
)


from cterasdk.core.files.common import (
    get_object_path,
    FetchResourcesParamBuilder,
    FetchResourcesResponse
)

from cterasdk.asynchronous.core import (
    query
)


from mcp.server.fastmcp import Context, FastMCP


logging.getLogger('cterasdk.core').disabled = True
logger = logging.getLogger(__name__)
logger.info("CTERA MCP Server Started")


@dataclass
class PortalContext:
    user: AsyncServicesPortal = None


@asynccontextmanager
async def ctera_lifespan(server: FastMCP) -> AsyncIterator[PortalContext]:
    user = AsyncServicesPortal(os.environ['CTERA_ADDR'])
    try:
        await user.login(os.environ['CTERA_USER'], os.environ['CTERA_PASS'])
        yield PortalContext(user=user)
    finally:
        await user.logout()


# Initialize FastMCP server
mcp = FastMCP("CTERA MCP Server", lifespan=ctera_lifespan)


@mcp.tool()
async def ctera_who_am_i(ctx: Context) -> str:
    """
    Get the current user's information.

    Returns:
        str: The current user's information.
    """
    user = ctx.request_context.lifespan_context.user
    session = await user.v1.api.get('/currentSession')
    
    username = session.username
    if session.domain:
        username = f'{username}@{session.domain}'
    
    return f'Authenticated as {username}'


@mcp.tool()
async def ctera_listdir(path: str, search_criteria: str = None, ctx: Context = None) -> list[str]:
    """
    List the contents of a specified directory.

    Args:
        path (str): The path to the directory to list.

    Returns:
        List[str]: A list of file and subdirectory names within the specified directory.
    """
    user = ctx.request_context.lifespan_context.user
    builder = FetchResourcesParamBuilder().root(get_object_path('/ServicesPortal/webdav', path).encoded_fullpath()).depth(1)
    if search_criteria:
        builder.searchCriteria(search_criteria)

    return [e.name async for e in query.iterator(user, '', builder.build(), 'fetchResources', callback_response=FetchResourcesResponse)]


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')


