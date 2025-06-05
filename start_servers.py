#!/usr/bin/env python3
"""
Startup script for CTERA MCP Core
Starts both:
1. MCP Server (SSE/stdio) on port 8001 for MCP clients
2. ChatGPT API on port 8003 for ChatGPT integration
"""
import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path

def set_environment_variables():
    """Set CTERA environment variables from mcp.json or defaults"""
    # Try to read from user's mcp.json first
    mcp_config_path = Path.home() / ".cursor" / "mcp.json"
    
    if mcp_config_path.exists():
        print("📄 Found mcp.json configuration")
        # In production, you might want to parse the JSON
        # For now, we'll use the known values
    
    # Set environment variables (these should be set externally in production)
    env_vars = {
        "ctera.mcp.core.settings.scope": "user",
        "ctera.mcp.core.settings.host": "hcpaw.ctera.me",
        "ctera.mcp.core.settings.user": "administrator", 
        "ctera.mcp.core.settings.password": "Password1!",
        "ctera.mcp.core.settings.ssl": "false"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Environment variables configured")

def start_mcp_server():
    """Start the MCP server on port 8001"""
    print("🚀 Starting MCP Server on port 8001...")
    return subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "src.main:app", 
        "--host", "0.0.0.0",
        "--port", "8001",
        "--reload"
    ])

def start_chatgpt_api():
    """Start the ChatGPT API on port 8003"""
    print("🤖 Starting ChatGPT API on port 8003...")
    return subprocess.Popen([
        sys.executable, "simple_ctera_api.py"
    ])

def main():
    print("=" * 60)
    print("🏢 CTERA MCP Core Server Startup")
    print("=" * 60)
    
    # Set environment variables
    set_environment_variables()
    
    try:
        # Start both servers
        mcp_process = start_mcp_server()
        time.sleep(2)  # Give MCP server time to start
        
        chatgpt_process = start_chatgpt_api()
        time.sleep(2)  # Give ChatGPT API time to start
        
        print("\n✅ Both servers started successfully!")
        print("\n📋 Server Information:")
        print("   🔗 MCP Server (SSE/stdio): http://localhost:8001")
        print("   🔗 ChatGPT API:           http://localhost:8003")
        print("\n📚 Available Endpoints:")
        print("   📊 MCP Status:    GET  http://localhost:8001/api/health")
        print("   🤖 ChatGPT Tools: GET  http://localhost:8003/tools")
        print("   👤 Who Am I:      POST http://localhost:8003/tools/who_am_i")
        print("   📁 List Dir:      POST http://localhost:8003/tools/list_dir")
        print("\n⏹️  Press Ctrl+C to stop both servers")
        
        # Wait for both processes
        while True:
            if mcp_process.poll() is not None:
                print("❌ MCP Server stopped unexpectedly")
                break
            if chatgpt_process.poll() is not None:
                print("❌ ChatGPT API stopped unexpectedly")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        
        if 'mcp_process' in locals():
            mcp_process.terminate()
        if 'chatgpt_process' in locals():
            chatgpt_process.terminate()
            
        print("✅ Servers stopped")

if __name__ == "__main__":
    main() 