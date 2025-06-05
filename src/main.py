from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from src.tools import mcp
from src.sse import create_sse_app
from src.tools_api import router as tool_router

app = FastAPI()

# Mount tool API routes under /api
app.include_router(tool_router, prefix="/api")

# Mount SSE server under /
sse_app = create_sse_app(mcp)
app.mount("/", sse_app)