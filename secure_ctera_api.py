#!/usr/bin/env python3
"""
Secure CTERA ChatGPT API Integration
Implements proper authentication and credential handling
"""
import asyncio
import os
import secrets
import hashlib
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
# import jwt  # Not needed for basic implementation

# Import CTERA components
from src.common import PortalContext, Env

app = FastAPI(
    title="Secure CTERA ChatGPT API", 
    version="1.0.0",
    description="Secure HTTP API for ChatGPT to interact with CTERA Portal",
    openapi_url=None  # Disable default OpenAPI
)

security = HTTPBearer()

# In-memory session store (use Redis in production)
active_sessions = {}

class UserCredentials(BaseModel):
    host: str
    user: str
    password: str
    scope: str = "user"
    ssl: bool = False

class SessionResponse(BaseModel):
    session_token: str
    expires_at: str
    message: str

class DirectoryRequest(BaseModel):
    path: str
    include_deleted: bool = False

class CreateDirectoryRequest(BaseModel):
    path: str

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def verify_session_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify session token and return session data"""
    token = credentials.credentials
    if token not in active_sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    
    session = active_sessions[token]
    if datetime.fromisoformat(session['expires_at']) < datetime.now():
        del active_sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")
    
    return session

async def get_portal_session(session_data: dict):
    """Get authenticated portal session using session credentials"""
    try:
        # Create environment from session credentials
        os.environ["ctera.mcp.core.settings.scope"] = session_data['credentials']['scope']
        os.environ["ctera.mcp.core.settings.host"] = session_data['credentials']['host']
        os.environ["ctera.mcp.core.settings.user"] = session_data['credentials']['user']
        os.environ["ctera.mcp.core.settings.password"] = session_data['credentials']['password']
        os.environ["ctera.mcp.core.settings.ssl"] = str(session_data['credentials']['ssl']).lower()
        
        env = Env.load()
        portal_context = PortalContext.initialize(env)
        await portal_context.login()
        return portal_context
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to CTERA: {str(e)}")

@app.post("/auth/login", response_model=SessionResponse)
async def login(credentials: UserCredentials):
    """Authenticate user and create session token"""
    try:
        # Test credentials by attempting to login
        os.environ["ctera.mcp.core.settings.scope"] = credentials.scope
        os.environ["ctera.mcp.core.settings.host"] = credentials.host
        os.environ["ctera.mcp.core.settings.user"] = credentials.user
        os.environ["ctera.mcp.core.settings.password"] = credentials.password
        os.environ["ctera.mcp.core.settings.ssl"] = str(credentials.ssl).lower()
        
        env = Env.load()
        portal_context = PortalContext.initialize(env)
        await portal_context.login()
        
        # Get user info for verification
        session = await portal_context.session.v1.api.get('/currentSession')
        username = session.username
        if session.domain:
            username = f'{username}@{session.domain}'
        
        await portal_context.logout()
        
        # Create session token
        session_token = generate_session_token()
        expires_at = datetime.now() + timedelta(hours=24)  # 24 hour session
        
        # Store session (in production, use encrypted database)
        active_sessions[session_token] = {
            'user': username,
            'credentials': {
                'scope': credentials.scope,
                'host': credentials.host,
                'user': credentials.user,
                'password': credentials.password,  # In production: encrypt this
                'ssl': credentials.ssl
            },
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        return SessionResponse(
            session_token=session_token,
            expires_at=expires_at.isoformat(),
            message=f"Successfully authenticated as {username}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@app.post("/auth/logout")
async def logout(session_data: dict = Depends(verify_session_token)):
    """Logout and invalidate session token"""
    # Find and remove the session token
    for token, session in list(active_sessions.items()):
        if session == session_data:
            del active_sessions[token]
            break
    
    return {"message": "Successfully logged out"}

@app.get("/chatgpt-openapi.json")
async def get_chatgpt_openapi():
    """Custom OpenAPI specification for ChatGPT with authentication"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Secure CTERA Portal API",
            "description": "Secure API for interacting with CTERA Portal file management system",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": "https://your-ngrok-url.ngrok.io",  # Update this!
                "description": "Secure CTERA API Server"
            }
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "Session token obtained from /auth/login"
                }
            }
        },
        "security": [
            {
                "bearerAuth": []
            }
        ],
        "paths": {
            "/auth/login": {
                "post": {
                    "summary": "Authenticate with CTERA credentials",
                    "description": "Login with CTERA credentials to obtain a session token",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "host": {"type": "string", "description": "CTERA host (e.g., portal.ctera.com)"},
                                        "user": {"type": "string", "description": "Username"},
                                        "password": {"type": "string", "description": "Password"},
                                        "scope": {"type": "string", "default": "user", "description": "Authentication scope"},
                                        "ssl": {"type": "boolean", "default": True, "description": "Use SSL"}
                                    },
                                    "required": ["host", "user", "password"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Authentication successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "session_token": {"type": "string"},
                                            "expires_at": {"type": "string"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "security": []
                }
            },
            "/tools/who_am_i": {
                "post": {
                    "summary": "Get current user information",
                    "description": "Returns information about the currently authenticated CTERA user",
                    "responses": {
                        "200": {
                            "description": "User information"
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
                                        "path": {"type": "string", "description": "Directory path"},
                                        "include_deleted": {"type": "boolean", "default": False}
                                    },
                                    "required": ["path"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Directory listing"
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
                                        "path": {"type": "string", "description": "Directory path"}
                                    },
                                    "required": ["path"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Directory created"
                        }
                    }
                }
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_sessions)
    }

@app.post("/tools/who_am_i")
async def who_am_i(session_data: dict = Depends(verify_session_token)):
    """Get current user information"""
    try:
        portal = await get_portal_session(session_data)
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
async def list_directory(request: DirectoryRequest, session_data: dict = Depends(verify_session_token)):
    """List directory contents"""
    try:
        portal = await get_portal_session(session_data)
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

@app.post("/tools/create_directory")
async def create_directory(request: CreateDirectoryRequest, session_data: dict = Depends(verify_session_token)):
    """Create a directory"""
    try:
        portal = await get_portal_session(session_data)
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
    """Get API status"""
    return {
        "status": "secure",
        "active_sessions": len(active_sessions),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 