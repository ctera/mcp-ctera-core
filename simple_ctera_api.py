#!/usr/bin/env python3
"""
CTERA ChatGPT API Integration
Provides HTTP endpoints for ChatGPT to interact with CTERA Portal
Runs independently from the MCP server (SSE/stdio)
"""
import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

# Import CTERA components
from src.common import PortalContext, Env

app = FastAPI(
    title="CTERA ChatGPT API", 
    version="1.0.0",
    description="HTTP API for ChatGPT to interact with CTERA Portal",
    openapi_url=None  # Disable default OpenAPI to use our custom one
)

# Environment variables should be set externally in production
# These are fallback defaults for development
if not os.environ.get("ctera.mcp.core.settings.host"):
    os.environ["ctera.mcp.core.settings.scope"] = "user"
    os.environ["ctera.mcp.core.settings.host"] = "hcpaw.ctera.me"
    os.environ["ctera.mcp.core.settings.user"] = "administrator"
    os.environ["ctera.mcp.core.settings.password"] = "Password1!"
    os.environ["ctera.mcp.core.settings.ssl"] = "false"

class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}

class DirectoryRequest(BaseModel):
    path: str
    include_deleted: bool = False

async def get_portal_session():
    """Get authenticated portal session"""
    env = Env.load()
    portal_context = PortalContext.initialize(env)
    await portal_context.login()
    return portal_context

@app.get("/chatgpt-openapi.json")
async def get_chatgpt_openapi():
    """Custom OpenAPI specification for ChatGPT"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "CTERA Portal API",
            "description": "API for interacting with CTERA Portal file management system",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": "https://your-ngrok-url.ngrok.io",  # Update this with your actual URL!
                "description": "CTERA API Server"
            }
        ],
        "paths": {
            "/tools/who_am_i": {
                "post": {
                    "summary": "Get current user information",
                    "description": "Returns information about the currently authenticated CTERA user",
                    "responses": {
                        "200": {
                            "description": "User information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "result": {"type": "string"},
                                            "username": {"type": "string"},
                                            "domain": {"type": "string"},
                                            "timestamp": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/tools/list_dir": {
                "post": {
                    "summary": "List directory contents",
                    "description": "Lists files and folders in a CTERA Portal directory",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "path": {
                                            "type": "string",
                                            "description": "Directory path to list (e.g., '/' for root)"
                                        },
                                        "include_deleted": {
                                            "type": "boolean",
                                            "default": False,
                                            "description": "Whether to include deleted files"
                                        }
                                    },
                                    "required": ["path"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Directory listing",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "result": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "name": {"type": "string"},
                                                        "is_dir": {"type": "boolean"},
                                                        "last_modified": {"type": "string"},
                                                        "deleted": {"type": "boolean"}
                                                    }
                                                }
                                            },
                                            "path": {"type": "string"},
                                            "count": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/tools/create_directory": {
                "post": {
                    "summary": "Create a new directory",
                    "description": "Creates a new directory in CTERA Portal",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "path": {
                                            "type": "string",
                                            "description": "Full path for the new directory"
                                        }
                                    },
                                    "required": ["path"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Directory created successfully"
                        }
                    }
                }
            },
            "/tools": {
                "get": {
                    "summary": "List available tools",
                    "description": "Returns a list of all available CTERA tools",
                    "responses": {
                        "200": {
                            "description": "List of available tools"
                        }
                    }
                }
            },
            "/status": {
                "get": {
                    "summary": "Get connection status",
                    "description": "Returns the status of the CTERA connection",
                    "responses": {
                        "200": {
                            "description": "Connection status"
                        }
                    }
                }
            },
            "/health": {
                "get": {
                    "summary": "Health check",
                    "description": "Returns the health status of the API",
                    "responses": {
                        "200": {
                            "description": "API is healthy"
                        }
                    }
                }
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/tools")
async def list_tools():
    """List available CTERA tools"""
    tools = [
        {"name": "who_am_i", "description": "Get current user information"},
        {"name": "list_dir", "description": "List directory contents", "parameters": ["path", "include_deleted"]},
        {"name": "create_directory", "description": "Create a directory", "parameters": ["path"]},
        {"name": "delete_items", "description": "Delete files/folders", "parameters": ["paths"]},
        {"name": "copy_item", "description": "Copy file/folder", "parameters": ["source", "destination"]},
        {"name": "move_item", "description": "Move file/folder", "parameters": ["source", "destination"]},
        {"name": "read_file", "description": "Read file contents", "parameters": ["path"]},
        {"name": "upload_file", "description": "Upload a file", "parameters": ["path", "destination"]},
    ]
    return {"tools": tools, "count": len(tools)}

@app.post("/tools/who_am_i")
async def who_am_i():
    """Get current user information"""
    try:
        portal = await get_portal_session()
        try:
            session = await portal.session.v1.api.get('/currentSession')
            username = session.username
            if session.domain:
                username = f'{username}@{session.domain}'
            result = f'Authenticated as {username}'
            return {
                "result": result,
                "username": username,
                "domain": getattr(session, 'domain', None),
                "timestamp": datetime.now().isoformat()
            }
        finally:
            await portal.logout()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/list_dir")
async def list_directory(request: DirectoryRequest):
    """List directory contents"""
    try:
        portal = await get_portal_session()
        try:
            iterator = await portal.session.files.listdir(request.path, include_deleted=request.include_deleted)
            files = []
            async for f in iterator:
                files.append({
                    'name': f.name,
                    'last_modified': f.lastmodified,
                    'deleted': f.isDeleted,
                    'is_dir': f.isFolder,
                    'id': getattr(f, 'fileId', None)
                })
            return {
                "result": files,
                "path": request.path,
                "count": len(files),
                "timestamp": datetime.now().isoformat()
            }
        finally:
            await portal.logout()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateDirectoryRequest(BaseModel):
    path: str

@app.post("/tools/create_directory")
async def create_directory(request: CreateDirectoryRequest):
    """Create a directory"""
    try:
        portal = await get_portal_session()
        try:
            await portal.session.files.mkdir(request.path)
            return {
                "result": f"Created directory: {request.path}",
                "path": request.path,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            await portal.logout()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Get connection status"""
    try:
        env = Env.load()
        return {
            "connected": True,
            "host": env.host,
            "scope": env.scope,
            "user": env.user,
            "ssl": env.ssl,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 