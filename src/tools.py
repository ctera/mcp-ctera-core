from mcp.server.fastmcp import Context
from common import mcp, with_session_refresh


@mcp.tool()
@with_session_refresh
async def ctera_portal_browse_team_portal(
    tenant: str, ctx: Context
) -> str:
    """
    Browse to a specific Team Portal tenant.
    
    Args:
        tenant: The name of the tenant to browse to
        ctx: MCP context for session management
        
    Returns:
        Success message or error if not authorized
        
    Raises:
        Requires global administrator privileges
    """
    user = ctx.request_context.lifespan_context.session
    if user.context != 'admin':
        return (
            'Context error: you must be a global administrator to browse '
            'Team Portal tenants.'
        )
    if user.session().current_tenant() == tenant:
        return (
            f'You are already operating within the scope of the '
            f'"{tenant}" tenant.'
        )
    await user.portals.browse(tenant)
    return f'Changed context to the "{tenant}" tenant.'


@mcp.tool()
@with_session_refresh
async def ctera_portal_browse_global_admin(
    ctx: Context
) -> str:
    """
    Browse to the global administration scope.
    
    Args:
        ctx: MCP context for session management
        
    Returns:
        Success message indicating context change or current state
    """
    user = ctx.request_context.lifespan_context.session
    if not user.session().in_tenant_context():
        return (
            'You are already operating within the global administration '
            'scope.'
        )
    await user.portals.browse_global_admin()
    return 'Changed context to global administration scope.'


@mcp.tool()
@with_session_refresh
async def ctera_portal_who_am_i(ctx: Context) -> str:
    """
    Get information about the currently authenticated user.
    
    Args:
        ctx: MCP context for session management
        
    Returns:
        Username and domain information of authenticated user
    """
    user = ctx.request_context.lifespan_context.session
    session = await user.v1.api.get('/currentSession')
    username = session.username
    if session.domain:
        username = f'{username}@{session.domain}'

    return f'Authenticated as {username}'


@mcp.tool()
@with_session_refresh
async def ctera_portal_list_dir(
    path: str, 
    ctx: Context,
    include_deleted: bool = False
) -> list[dict]:
    """
    List the contents of a directory in the CTERA Portal.
    
    Args:
        path: Directory path to list
        include_deleted: Whether to include deleted files
        ctx: MCP context for session management
        
    Returns:
        List of dictionaries containing file/folder information
    """
    user = ctx.request_context.lifespan_context.session
    iterator = await user.files.listdir(
        path, include_deleted=include_deleted
    )

    return [{
        'name': f.name,
        'last_modified': f.lastmodified,
        'deleted': f.isDeleted,
        'is_dir': f.isFolder,
        'id': getattr(f, 'fileId', None)
    } async for f in iterator]


@mcp.tool()
@with_session_refresh
async def ctera_portal_create_directory(
    path: str, ctx: Context
) -> str:
    """
    Create a new directory in the CTERA Portal.
    
    Args:
        path: Path where the directory should be created
        ctx: MCP context for session management
        
    Returns:
        Success message with created directory path
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.mkdir(path)
    return f"Created: {path}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_copy_item(
    source: str, 
    destination: str, 
    ctx: Context
) -> str:
    """
    Copy a file or directory to a new location.
    
    Args:
        source: Source file or directory path
        destination: Destination path for the copy
        ctx: MCP context for session management
        
    Returns:
        Success message with source and destination paths
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.copy(source, destination=destination)
    return f"Copied: {source} to: {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_move_item(
    source: str, 
    destination: str, 
    ctx: Context
) -> str:
    """
    Move a file or directory to a new location.
    
    Args:
        source: Source file or directory path  
        destination: Destination path for the move
        ctx: MCP context for session management
        
    Returns:
        Success message with source and destination paths
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.move(source, destination=destination)
    return f"Moved: {source} to {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_rename_item(
    path: str, 
    new_name: str, 
    ctx: Context
) -> str:
    """
    Rename a file or directory.
    
    Args:
        path: Current path of the file or directory
        new_name: New name for the file or directory
        ctx: MCP context for session management
        
    Returns:
        Success message with old and new names
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.rename(path, new_name)
    return f"Renamed: {path} to: {new_name}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_delete_items(
    paths: list[str], ctx: Context
) -> str:
    """
    Delete multiple files or directories.
    
    Args:
        paths: List of file or directory paths to delete
        ctx: MCP context for session management
        
    Returns:
        Success message with list of deleted paths
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.delete(*paths)
    return f"Deleted: {list(paths)}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_recover_items(
    paths: list[str], ctx: Context
) -> str:
    """
    Recover previously deleted files or directories.
    
    Args:
        paths: List of file or directory paths to recover
        ctx: MCP context for session management
        
    Returns:
        Success message with list of recovered paths
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.undelete(*paths)
    return f"Recovered: {list(paths)}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_list_versions(
    path: str, ctx: Context
) -> list:
    """
    List all versions of a specific file.
    
    Args:
        path: Path to the file
        ctx: MCP context for session management
        
    Returns:
        List of version timestamps for the file
    """
    user = ctx.request_context.lifespan_context.session
    versions = await user.files.versions(path)
    return [version.startTimestamp for version in versions]


@mcp.tool()
@with_session_refresh
async def ctera_portal_create_public_link(
    path: str, 
    ctx: Context,
    access: str = 'RO', 
    expire_in: int = 30
) -> dict:
    """
    Create a public link for sharing a file or directory.
    
    Args:
        path: Path to the file or directory to share
        access: Access level ('RO' for read-only, 'RW' for read-write)
        expire_in: Number of days until the link expires
        ctx: MCP context for session management
        
    Returns:
        Dictionary containing public link information
    """
    user = ctx.request_context.lifespan_context.session
    public_link = await user.files.public_link(
        path, access=access, expire_in=expire_in
    )
    return public_link


@mcp.tool()
@with_session_refresh
async def ctera_portal_get_permalink(
    path: str, ctx: Context
) -> str:
    """
    Get a permanent link to a file or directory.
    
    Args:
        path: Path to the file or directory
        ctx: MCP context for session management
        
    Returns:
        Permanent link URL as a string
    """
    user = ctx.request_context.lifespan_context.session
    permalink = await user.files.permalink(path)
    return permalink


@mcp.tool()
@with_session_refresh
async def ctera_portal_download_file(
    path: str, 
    destination: str, 
    ctx: Context
) -> str:
    """
    Download a file from the CTERA Portal to local storage.
    
    Args:
        path: Remote file path in CTERA Portal
        destination: Local destination path for the download
        ctx: MCP context for session management
        
    Returns:
        Success message with source and destination paths
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.download(path, destination=destination)
    return f"Downloaded: {path} to: {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_read_file(
    path: str, ctx: Context
) -> str:
    """
    Read the contents of a text file from the CTERA Portal.
    
    Args:
        path: Path to the file to read
        ctx: MCP context for session management
        
    Returns:
        Text content of the file as a string
    """
    user = ctx.request_context.lifespan_context.session
    handle = await user.files.handle(path)
    text_content = await handle.text()
    return text_content


@mcp.tool()
@with_session_refresh
async def ctera_portal_upload_from_content(
    filepath: str, 
    content: str | bytes, 
    ctx: Context
) -> str:
    """
    Upload content directly to the CTERA Portal as a file.
    
    Args:
        filepath: Destination file path in CTERA Portal
        content: Content to upload (string or bytes)
        ctx: MCP context for session management
        
    Returns:
        Success message with uploaded file path
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.upload('', filepath, content)
    return f"Uploaded: {filepath}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_upload_file(
    path: str, 
    destination: str, 
    ctx: Context
) -> str:
    """
    Upload a local file to the CTERA Portal.
    
    Args:
        path: Local file path to upload
        destination: Destination path in CTERA Portal
        ctx: MCP context for session management
        
    Returns:
        Success message with source and destination paths
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.upload_file(path, destination)
    return f"Uploaded: {path} to: {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_makedirs(
    path: str, ctx: Context
) -> str:
    """
    Create a directory and all necessary parent directories.
    
    Args:
        path: Directory path to create (including parents)
        ctx: MCP context for session management
        
    Returns:
        Success message with created directory path
    """
    user = ctx.request_context.lifespan_context.session
    await user.files.makedirs(path)
    return f"Created: {path}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_walk_tree(
    path: str, 
    ctx: Context,
    include_deleted: bool = False
) -> list:
    """
    Recursively walk through a directory tree.
    
    Args:
        path: Root directory path to start walking from
        include_deleted: Whether to include deleted files and directories
        ctx: MCP context for session management
        
    Returns:
        List of dictionaries containing information about all files and
        directories in the tree
    """
    user = ctx.request_context.lifespan_context.session
    iterator = await user.files.walk(
        path, include_deleted=include_deleted
    )
    return [{
        'name': f.name,
        'href': f.href,
        'lastmodified': f.lastmodified,
        'isFolder': f.isFolder,
        'isDeleted': f.isDeleted,
        'fileId': getattr(f, 'fileId', None)
    } async for f in iterator]
