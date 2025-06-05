from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from .tools import mcp

app = FastAPI()


def create_sse_app(mcp_server: FastMCP):
    """Create a Starlette app that serves MCP over SSE."""
    transport = SseServerTransport("/messages")
    
    async def handle_sse(request):
        """Handle SSE connections."""
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_server.run(
                streams[0], streams[1]
            )

    async def handle_messages(request):
        """Handle HTTP POST messages."""
        return await transport.handle_post_message(request.scope, request.receive, request._send)

    # Create Starlette routes
    routes = [
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]

    return Starlette(routes=routes)


app.mount('/', create_sse_app(mcp))
