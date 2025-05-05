import os
import logging
import functools
import cterasdk.settings
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Callable, Any

from cterasdk import (
    AsyncServicesPortal
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
    # Configure SSL settings for untrusted/self-signed certificates
    cterasdk.settings.sessions.management.ssl = False    
    user = AsyncServicesPortal(os.environ['CTERA_ADDR'])
    try:
        await user.login(os.environ['CTERA_USER'], os.environ['CTERA_PASS'])
        yield PortalContext(user=user)
    finally:
        await user.logout()


# Session refresh decorator
def with_session_refresh(func: Callable) -> Callable:
    """
    Decorator to handle session expiration and automatic refresh.
    
    Args:
        func: The function to wrap with session refresh logic
        
    Returns:
        Wrapped function that handles session refresh
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract context from args or kwargs
        ctx = kwargs.get('ctx')
        if ctx is None:
            for arg in args:
                if isinstance(arg, Context):
                    ctx = arg
                    break
        
        if ctx is None:
            raise ValueError("Context not found in function arguments")
        
        user = ctx.request_context.lifespan_context.user
        
        try:
            # Try the original function
            return await func(*args, **kwargs)
        except Exception as e:
            # Check if it's a session expired error
            error_msg = str(e).lower()
            if "session expired" in error_msg or "session invalid" in error_msg:
                logger.info("Session expired, refreshing...")
                # Re-authenticate
                await user.login(os.environ['CTERA_USER'], os.environ['CTERA_PASS'])
                # Retry the function
                return await func(*args, **kwargs)
            else:
                # If it's another error, re-raise it
                raise
    
    return wrapper


# Initialize FastMCP server
mcp = FastMCP("CTERA MCP Server", lifespan=ctera_lifespan)


@mcp.tool()
@with_session_refresh
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
@with_session_refresh
async def ctera_list_dir(path: str, search_criteria: str = None, include_deleted: bool = False, ctx: Context = None) -> list[dict]:
    """
    List the contents of a specified directory.

    Args:
        path (str): The path to the directory to list.
        search_criteria (str, optional): Search criteria to filter results.
        include_deleted (bool, optional): Include deleted files in the results. Defaults to False.

    Returns:
        List[dict]: A list of dictionaries containing file information with 'name', 'lastmodified', 'isDeleted', and 'isFolder' keys.
    """
    user = ctx.request_context.lifespan_context.user
    
    if include_deleted:
        files_iterator = await user.files.listdir(path, include_deleted=True)
    else:
        files_iterator = await user.files.listdir(path)
    
    # Filter by search criteria if provided
    if search_criteria:
        return [{"name": file.name, "lastmodified": file.lastmodified, "isDeleted": file.isDeleted, "isFolder": file.isFolder} async for file in files_iterator if search_criteria in file.name]
    
    return [{"name": file.name, "lastmodified": file.lastmodified, "isDeleted": file.isDeleted, "isFolder": file.isFolder} async for file in files_iterator]


@mcp.tool()
@with_session_refresh
async def ctera_create_directory(path: str, ctx: Context = None) -> str:
    """
    Create a new directory at the specified path.

    Args:
        path (str): The path where the directory should be created.
        ctx: Request context

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    await user.files.mkdir(path)
    
    return f"Directory created successfully at path: {path}"


@mcp.tool()
@with_session_refresh
async def ctera_copy_item(source_path: str, destination_path: str, ctx: Context = None) -> str:
    """
    Copy a file or folder to a destination path.

    Args:
        source_path (str): The path of the file or folder to copy.
        destination_path (str): The destination path where the item should be copied to.
        ctx: Request context

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    await user.files.copy(source_path, destination=destination_path)
    
    return f"Successfully copied {source_path} to {destination_path}"


@mcp.tool()
@with_session_refresh
async def ctera_move_item(source_path: str, destination_path: str, ctx: Context = None) -> str:
    """
    Move a file or folder to a destination path.

    Args:
        source_path (str): The path of the file or folder to move.
        destination_path (str): The destination path where the item should be moved to.
        ctx: Request context

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    await user.files.move(source_path, destination=destination_path)
    
    return f"Successfully moved {source_path} to {destination_path}"


@mcp.tool()
@with_session_refresh
async def ctera_rename_item(path: str, new_name: str, ctx: Context = None) -> str:
    """
    Rename a file or folder.

    Args:
        path (str): The path of the file or folder to rename.
        new_name (str): The new name for the file or folder (not full path).
        ctx: Request context

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    await user.files.rename(path, new_name)
    
    return f"Successfully renamed {path} to {new_name}"


@mcp.tool()
@with_session_refresh
async def ctera_delete_item(path: str, ctx: Context = None) -> str:
    """
    Delete a file or folder.

    Args:
        path (str): The path of the file or folder to delete.
        ctx: Request context

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    await user.files.delete(path)
    
    return f"Successfully deleted {path}"


@mcp.tool()
@with_session_refresh
async def ctera_delete_items(paths: list[str], ctx: Context = None) -> str:
    """
    Delete multiple files or folders at once.

    Args:
        paths (list[str]): A list of paths to files or folders to delete.
        ctx: Request context

    Examples:
        # Delete multiple files
        ctera_delete_items(['My Files/newfolder/index2.html', '/My Files/newfolder/sub1/sub2/index.html'])

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    # Convert the list to a tuple of path arguments
    await user.files.delete(*paths)
    
    paths_str = ", ".join(paths)
    return f"Successfully deleted multiple items: {paths_str}"


@mcp.tool()
@with_session_refresh
async def ctera_recover_item(path: str, ctx: Context = None) -> str:
    """
    Recover a deleted file or folder.

    Args:
        path (str): The path of the file or folder to recover.
        ctx: Request context

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    await user.files.undelete(path)
    
    return f"Successfully recovered {path}"


@mcp.tool()
@with_session_refresh
async def ctera_recover_items(paths: list[str], ctx: Context = None) -> str:
    """
    Recover multiple deleted files or folders at once.

    Args:
        paths (list[str]): A list of paths to files or folders to recover.
        ctx: Request context

    Examples:
        # Recover multiple files
        ctera_recover_items(['My Files/newfolder/index2.html', '/My Files/newfolder/sub1/sub2/index.html'])

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    # Convert the list to a tuple of path arguments
    await user.files.undelete(*paths)
    
    paths_str = ", ".join(paths)
    return f"Successfully recovered multiple items: {paths_str}"


@mcp.tool()
@with_session_refresh
async def ctera_list_versions(path: str, ctx: Context = None) -> list:
    """
    List all available versions of a file.

    Args:
        path (str): The path of the file to list versions for.
        ctx: Request context

    Returns:
        list: List of timestamps for each version and their URLs
    """
    user = ctx.request_context.lifespan_context.user
    
    versions = await user.files.versions(path)
    
    # Extract the startTimestamp from each version
    return [version.startTimestamp for version in versions]


@mcp.tool()
@with_session_refresh
async def ctera_create_public_link(path: str, access: str = 'RO', expire_in: int = 30, ctx: Context = None) -> dict:
    """
    Create a public link to a file or folder.

    Args:
        path (str): The path of the file or folder to create a link for.
        access (str, optional): Access policy of the link, defaults to 'RO' (read-only).
                               Use 'RW' for read-write access.
        expire_in (int, optional): Number of days until the link expires, defaults to 30.
        ctx: Request context

    Returns:
        dict: Information about the created public link
    """
    user = ctx.request_context.lifespan_context.user
    
    public_link = await user.files.public_link(path, access=access, expire_in=expire_in)
    
    return public_link


@mcp.tool()
@with_session_refresh
async def ctera_get_permalink(path: str, ctx: Context = None) -> str:
    """
    Get a permanent link to a file or folder.

    Args:
        path (str): The path of the file or folder to get a permalink for.
        ctx: Request context

    Returns:
        str: Permalink to the file or folder
    """
    user = ctx.request_context.lifespan_context.user
    
    permalink = await user.files.permalink(path)
    
    return permalink


@mcp.tool()
@with_session_refresh
async def ctera_read_file(path: str, ctx: Context = None) -> str:
    """
    Read the content of a text file.

    Args:
        path (str): The path of the text file to read.
        ctx: Request context

    Returns:
        str: Text content of the file
    """
    user = ctx.request_context.lifespan_context.user
    
    # Get file handle and read text content
    handle = await user.files.handle(path)
    text_content = await handle.text()
    
    return text_content


@mcp.tool()
@with_session_refresh
async def ctera_upload_file(local_file_path: str, target_directory: str, ctx: Context = None) -> str:
    """
    Upload a file to CTERA.

    Args:
        local_file_path (str): The full path to the local file to upload (e.g., '/path/to/myfile.txt')
        target_directory (str): The CTERA directory where the file should be uploaded (e.g., 'My Files/Documents/')
                               The directory must end with a trailing slash.
        ctx: Request context

    Examples:
        # Upload a local file to the root of My Files
        ctera_upload_file('/home/user/document.pdf', 'My Files/')
        
        # Upload to a subdirectory
        ctera_upload_file('/home/user/picture.jpg', 'My Files/Photos/')

    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    # Ensure target_directory ends with a trailing slash
    if not target_directory.endswith('/'):
        target_directory += '/'
    
    # Upload the file
    await user.files.upload_file(local_file_path, destination=target_directory)
    
    return f"Successfully uploaded {local_file_path} to {target_directory}"


@mcp.tool()
@with_session_refresh
async def ctera_makedirs(path: str, ctx: Context = None) -> str:
    """
    Create directories recursively, creating parent directories as needed.
    
    This function will create all directories in the path that don't exist,
    similar to os.makedirs() in Python.
    
    Args:
        path (str): The full directory path to create (e.g., 'My Files/folder1/folder2/folder3').
        ctx: Request context
        
    Examples:
        # Create a nested directory structure
        ctera_makedirs('My Files/newfolder/sub1/sub2/sub3')
        
    Returns:
        str: Success message
    """
    user = ctx.request_context.lifespan_context.user
    
    # Use the built-in makedirs method from the SDK
    await user.files.makedirs(path)
    
    return f"Successfully created directory structure: {path}"


@mcp.tool()
@with_session_refresh
async def ctera_walk_tree(path: str, ctx: Context = None) -> list:
    """
    Recursively list all files and folders in a directory tree.

    Args:
        path (str): The path of the directory to walk.
        ctx: Request context

    Returns:
        list: List of dictionaries with 'name' and 'href' for each file/folder
    """
    user = ctx.request_context.lifespan_context.user
    
    folder_tree = await user.files.walk(path)
    
    results = []
    async for file in folder_tree:
        results.append({
            'name': file.name,
            'href': file.href,
            'lastmodified': file.lastmodified,
            'isFolder': file.isFolder,
            'isDeleted': file.isDeleted,
        })
    
    return results


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')


