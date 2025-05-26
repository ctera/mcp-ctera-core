from mcp.server.fastmcp import Context
from common import mcp, with_session_refresh


@mcp.tool()
@with_session_refresh
async def ctera_portal_browse_team_portal(tenant: str, ctx: Context) -> str:
    user = ctx.request_context.lifespan_context.session
    if user.context != 'admin':
        return 'Context error: you must be a global administrator to browse Team Portal tenants.'
    if user.session().current_tenant() == tenant:
        return f'You are already operating within the scope of the "{tenant}" tenant.'
    await user.portals.browse(tenant)
    return f'Changed context to the "{tenant}" tenant.'


@mcp.tool()
@with_session_refresh
async def ctera_portal_browse_global_admin(ctx: Context) -> str:
    user = ctx.request_context.lifespan_context.session
    if not user.session().in_tenant_context():
        return f'You are already operating within the global administration scope.'
    await user.portals.browse_global_admin()


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
async def ctera_portal_copy_item(
    source: str, destination: str, ctx: Context = None
) -> str:
    user = ctx.request_context.lifespan_context.session
    await user.files.copy(source, destination=destination)
    return f"Copied: {source} to: {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_move_item(
    source: str, destination: str, ctx: Context = None
) -> str:
    user = ctx.request_context.lifespan_context.session
    await user.files.move(source, destination=destination)
    return f"Moved: {source} to {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_rename_item(
    path: str, new_name: str, ctx: Context = None
) -> str:
    user = ctx.request_context.lifespan_context.session
    await user.files.rename(path, new_name)
    return f"Renamed: {path} to: {new_name}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_delete_items(
    paths: list[str], ctx: Context = None
) -> str:
    user = ctx.request_context.lifespan_context.session
    await user.files.delete(*paths)
    return f"Deleted: {list(paths)}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_recover_item(path: str, ctx: Context = None) -> str:
    user = ctx.request_context.lifespan_context.session
    await user.files.undelete(path)
    return f"Recovered: {path}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_recover_items(
    paths: list[str], ctx: Context = None
) -> str:
    user = ctx.request_context.lifespan_context.session
    await user.files.undelete(*paths)
    return f"Recovered: {list(paths)}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_list_versions(path: str, ctx: Context = None) -> list:
    user = ctx.request_context.lifespan_context.session
    versions = await user.files.versions(path)
    return [version.startTimestamp for version in versions]


@mcp.tool()
@with_session_refresh
async def ctera_portal_create_public_link(
    path: str, access: str = 'RO', expire_in: int = 30, ctx: Context = None
) -> dict:
    user = ctx.request_context.lifespan_context.session
    public_link = await user.files.public_link(
        path, access=access, expire_in=expire_in
    )
    return public_link


@mcp.tool()
@with_session_refresh
async def ctera_portal_get_permalink(path: str, ctx: Context = None) -> str:
    user = ctx.request_context.lifespan_context.session
    permalink = await user.files.permalink(path)
    return permalink


@mcp.tool()
@with_session_refresh
async def ctera_portal_download_file(path: str, destination: str, ctx: Context = None) -> str:
    user = ctx.request_context.lifespan_context.session
    await user.files.download(path, destination=destination)
    return f"Downloaded: {path} to: {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_read_file(path: str, ctx: Context = None) -> str:
    user = ctx.request_context.lifespan_context.session
    handle = await user.files.handle(path)
    text_content = await handle.text()
    return text_content


@mcp.tool()
@with_session_refresh
async def ctera_portal_upload_file(path: str, destination: str, ctx: Context = None) -> str:
    user = ctx.request_context.lifespan_context.session
    await user.files.upload_file(path, destination)
    return f"Uploaded: {path} to: {destination}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_makedirs(path: str, ctx: Context = None) -> str:
    user = ctx.request_context.lifespan_context.session
    await user.files.makedirs(path)
    return f"Created: {path}"


@mcp.tool()
@with_session_refresh
async def ctera_portal_walk_tree(
    path: str, include_deleted: bool = False, ctx: Context = None
) -> list:
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
