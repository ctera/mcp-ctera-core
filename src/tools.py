from mcp.server.fastmcp import Context
from common import mcp, with_session_refresh


@mcp.tool()
@with_session_refresh
async def ctera_portal_who_am_i(ctx: Context) -> str:
    user = ctx.request_context.lifespan_context.session

    session = await user.v1.api.get('/currentSession')

    username = session.username
    if session.domain:
        username = f'{username}@{session.domain}'

    return f'Authenticated as {username}'


@mcp.tool()
@with_session_refresh
async def ctera_portal_list_dir(path: str, include_deleted: bool = False, ctx: Context = None) -> list[dict]:
    user = ctx.request_context.lifespan_context.session
    iterator = await user.files.listdir(path, include_deleted=include_deleted)

    return [{
        'name': f.name,
        'last_modified': f.lastmodified,
        'deleted': f.isDeleted,
        'is_dir': f.isFolder,
        'id': getattr(f, 'fileId', None)
    } async for f in iterator]


@mcp.tool()
@with_session_refresh
async def ctera_portal_create_directory(path: str, ctx: Context = None) -> str:
    user = ctx.request_context.lifespan_context.session
    await user.files.mkdir(path)
    return f"Created: {path}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_copy_item(source: str, destination: str, ctx: Context = None) -> str:
    """
    Copy a file or folder from one location to another.

    Args:
        source: The path of the file or folder to copy.
        destination: The path where the file or folder will be copied.
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.copy(source, destination=destination)
    return f"Copied: {source} to: {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_move_item(source: str, destination: str, ctx: Context = None) -> str:
    """
    Move a file or folder from one location to another.

    Args:
        source: The path of the file or folder to move.
        destination: The path where the file or folder will be moved.
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.move(source, destination=destination)
    return f"Moved: {source} to {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_rename_item(path: str, new_name: str, ctx: Context = None) -> str:
    """
    Rename a file or folder.

    Args:
        path: The path of the file or folder to rename.
        new_name: The new name for the file or folder.
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.rename(path, new_name)
    return f"Renamed: {path} to: {new_name}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_delete_items(paths: list[str], ctx: Context = None) -> str:
    """
    Delete a file or folder.

    Args:
        paths: The paths of the files or folders to delete.
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.delete(*paths)
    return f"Deleted: {list(paths)}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_recover_item(path: str, ctx: Context = None) -> str:
    """
    Recover a deleted file or folder.

    Args:
        path: The path of the file or folder to recover.
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.undelete(path)
    return f"Recovered: {path}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_recover_items(paths: list[str], ctx: Context = None) -> str:
    """
    Recover multiple deleted files or folders.

    Args:
        paths: The paths of the files or folders to recover.
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.undelete(*paths)
    return f"Recovered: {list(paths)}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_list_versions(path: str, ctx: Context = None) -> list:
    """
    List the versions of a file.

    Args:
        path: The path of the file to list versions for.
    """
    user = ctx.request_context.lifespan_context.session
    versions = await user.files.versions(path)
    return [version.startTimestamp for version in versions]


@mcp.tool()
@with_session_refresh
async def ctera_portal_create_public_link(
    path: str, access: str = 'RO', expire_in: int = 30, ctx: Context = None) -> dict:
    """
    Create a public link for a file or folder.

    Args:
        path: The path of the file or folder to create a public link for.
        access: The access level for the public link.
        expire_in: The number of days the public link will be valid for.
    """
    user = ctx.request_context.lifespan_context.session
    public_link = await user.files.public_link(
        path, access=access, expire_in=expire_in
    )
    return public_link


@mcp.tool()
@with_session_refresh
async def ctera_portal_get_permalink(path: str, ctx: Context = None) -> str:
    """
    Get a permalink for a file or folder.

    Args:
        path: The path of the file or folder to get a permalink for.
    """
    user = ctx.request_context.lifespan_context.session
    permalink = await user.files.permalink(path)
    return permalink


@mcp.tool()
@with_session_refresh
async def ctera_portal_read_file(path: str, ctx: Context = None) -> str:
    """
    Read the contents of a file.

    Args:
        path: The path of the file to read.
    """
    user = ctx.request_context.lifespan_context.session
    handle = await user.files.handle(path)
    text_content = await handle.text()
    return text_content


@mcp.tool()
@with_session_refresh
async def ctera_portal_upload_file(
    path: str, destination: str, ctx: Context = None
) -> str:
    """
    Upload a file to a destination.

    Args:
        path: The path of the file to upload.
        destination: The path where the file will be uploaded.
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.upload_file(path, destination=destination)
    return f"Uploaded: {path} to: {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_makedirs(path: str, ctx: Context = None) -> str:
    """
    Create a directory.

    Args:
        path: The path of the directory to create.
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.makedirs(path)
    return f"Created: {path}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_walk_tree(
    path: str, include_deleted: bool = False, ctx: Context = None) -> list:
    """
    Walk the tree of a directory.

    Args:
        path: The path of the directory to walk.
        include_deleted: Whether to include deleted files and folders.
    """
    user = ctx.request_context.lifespan_context.session
    iterator = await user.files.walk(path, include_deleted=include_deleted)
    return [{
        'name': f.name,
        'href': f.href,
        'lastmodified': f.lastmodified,
        'isFolder': f.isFolder,
        'isDeleted': f.isDeleted,
        'fileId': getattr(f, 'fileId', None)
    } async for f in iterator]
