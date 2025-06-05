from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .tools import mcp

router = APIRouter()

@router.get("/health")
async def health_check():
    return JSONResponse({"status": "ok"})

@router.get("/tools")
async def list_tools():
    """List all available MCP tools"""
    tools = []
    for tool in mcp.tools:
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        })
    return JSONResponse({"tools": tools})

@router.post("/tool")
async def run_tool(request: Request):
    """Execute an MCP tool via the MCP server"""
    try:
        payload = await request.json()
        tool_name = payload.get("tool_name")
        arguments = payload.get("arguments", {})
        
        # Find the tool
        tool = None
        for t in mcp.tools:
            if t.name == tool_name:
                tool = t
                break
                
        if not tool:
            return JSONResponse(
                {"error": f"Tool '{tool_name}' not found"}, 
                status_code=404
            )
        
        # This approach won't work because we need proper MCP context
        # For now, return an informative error
        return JSONResponse({
            "error": "MCP tools require proper context initialization. Use the SSE endpoint instead.",
            "available_via": "/sse",
            "tool_found": tool_name,
            "parameters_expected": tool.parameters
        }, status_code=501)
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)