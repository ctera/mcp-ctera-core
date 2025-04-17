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
    FetchResourcesResponse,
    get_create_dir_param,
    ActionResourcesParam,
    SrcDstParam,
    Path
)

from cterasdk.common import (
    Object
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
async def ctera_list_dir(path: str, search_criteria: str = None, ctx: Context = None) -> list[str]:
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

@mcp.tool()
async def ctera_create_folder(ctx: Context, folder_name: str, parent_path: str = "/") -> str:
    """
    Create a new folder at the specified path.

    Args:
        ctx: Request context
        folder_name: Name of the folder to create
        parent_path: Path where the folder should be created (default: "/")

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    full_path = get_object_path('/ServicesPortal/webdav', parent_path)
    param = get_create_dir_param(folder_name, full_path.encoded_fullpath())
    
    await user.v1.api.execute('', 'makeCollection', param)
    return f"Folder '{folder_name}' created successfully at '{parent_path}'"

@mcp.tool()
async def ctera_move_item(ctx: Context, source_path: str, destination_path: str) -> str:
    """
    Move a file or directory to a new location.

    Args:
        ctx: Request context
        source_path: Path of the file or directory to move (without leading slash)
        destination_path: Destination directory path (without leading slash)

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    # Remove leading slashes if present
    source_path = source_path.lstrip('/')
    destination_path = destination_path.lstrip('/')
    
    # Create Path objects for source and destination
    # The second parameter is the base path ('/ServicesPortal/webdav')
    src_path = Path(source_path, "/ServicesPortal/webdav")
    dst_path = Path(destination_path, "/ServicesPortal/webdav")
    
    # Create action parameters
    param = ActionResourcesParam.instance()
    
    # The destination should be the destination directory path + the source filename
    # Using joinpath to properly handle this
    param.add(SrcDstParam.instance(
        src=src_path.fullpath(),
        dest=dst_path.joinpath(src_path.name()).fullpath()
    ))
    
    # Execute the move operation
    await user.v1.api.execute('', 'moveResources', param)
    
    return f"Successfully moved '{source_path}' to '{destination_path}'"

@mcp.tool()
async def ctera_copy_item(ctx: Context, source_path: str, destination_path: str) -> str:
    """
    Copy a file or directory to a new location.

    Args:
        ctx: Request context
        source_path: Path of the file or directory to copy (without leading slash)
        destination_path: Destination directory path (without leading slash)

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    # Remove leading slashes if present
    source_path = source_path.lstrip('/')
    destination_path = destination_path.lstrip('/')
    
    # Create Path objects for source and destination
    # The second parameter is the base path ('/ServicesPortal/webdav')
    src_path = Path(source_path, "/ServicesPortal/webdav")
    dst_path = Path(destination_path, "/ServicesPortal/webdav")
    
    # Create action parameters
    param = ActionResourcesParam.instance()
    
    # The destination should be the destination directory path + the source filename
    # Using joinpath to properly handle this
    param.add(SrcDstParam.instance(
        src=src_path.fullpath(),
        dest=dst_path.joinpath(src_path.name()).fullpath()
    ))
    
    # Execute the copy operation
    await user.v1.api.execute('', 'copyResources', param)
    
    return f"Successfully copied '{source_path}' to '{destination_path}'"

@mcp.tool()
async def ctera_delete_item(ctx: Context, path: str) -> str:
    """
    Delete a file or directory.

    Args:
        ctx: Request context
        path: Path of the file or directory to delete (without leading slash)

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    # Remove leading slash if present
    path = path.lstrip('/')
    
    # Create Path object for the target
    # The second parameter is the base path ('/ServicesPortal/webdav')
    target_path = Path(path, "/ServicesPortal/webdav")
    
    # Create action parameters
    param = ActionResourcesParam.instance()
    
    # Add the path to delete
    param.add(SrcDstParam.instance(src=target_path.fullpath()))
    
    # Execute the delete operation
    await user.v1.api.execute('', 'deleteResources', param)
    
    return f"Successfully deleted '{path}'"

@mcp.tool()
async def ctera_rename_item(ctx: Context, path: str, new_name: str) -> str:
    """
    Rename a file or directory.

    Args:
        ctx: Request context
        path: Path of the file or directory to rename (without leading slash)
        new_name: New name for the file or directory (without path)

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    # Remove leading slash if present
    path = path.lstrip('/')
    
    # Create Path object for the source
    src_path = Path(path, "/ServicesPortal/webdav")
    
    # Get the parent directory of the source
    parent_path = src_path.parent()
    
    # Create action parameters
    param = ActionResourcesParam.instance()
    
    # The destination is the parent directory plus the new name
    param.add(SrcDstParam.instance(
        src=src_path.fullpath(),
        dest=parent_path.joinpath(new_name).fullpath()
    ))
    
    # Execute the rename operation (uses moveResources)
    await user.v1.api.execute('', 'moveResources', param)
    
    return f"Successfully renamed '{path}' to '{new_name}'"

@mcp.tool()
async def ctera_recover_item(ctx: Context, path: str) -> str:
    """
    Recover a deleted file or directory.

    Args:
        ctx: Request context
        path: Path of the file or directory to recover (without leading slash)

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    # Remove leading slash if present
    path = path.lstrip('/')
    
    # Create Path object for the target
    # The second parameter is the base path ('/ServicesPortal/webdav')
    target_path = Path(path, "/ServicesPortal/webdav")
    
    # Create action parameters
    param = ActionResourcesParam.instance()
    
    # Add the path to recover
    param.add(SrcDstParam.instance(src=target_path.fullpath()))
    
    # Execute the recover operation
    await user.v1.api.execute('', 'restoreResources', param)
    
    return f"Successfully recovered '{path}'"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')


