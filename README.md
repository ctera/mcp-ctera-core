# MCP Server for CTERA Portal

**mcp-server-ctera** provides an AI-powered interface to interact with the CTERA Intelligent Data Services Platform, using Model Context Protocol (MCP). This integration enables access to the file management APIs of CTERA Portal, allowing you to perform operations through natural language or automation workflows.

---

## 🔧 Features

- Integration with CTERA Portal APIs for file and folder management
- AI-driven command execution via MCP
- Configurable with environment variables for secure credentials
- Easily extensible to support more CTERA functions

---

## 🚀 Getting Started

To run this server, ensure you have the [MCP runtime](https://modelcontextprotocol.io/quickstart/user) installed and follow the configuration steps below.

---

## 🧩 MCP Server Configuration

Configuration using Standard I/O:

```json
{
    "mcpServers": {
      "ctera-core-mcp-server-stdio": {
        "command": "uv",
        "args": [
          "--directory",
          "C:\\Users\\saimon\\Desktop\\dev\\mcp-ctera-core\\src",
          "run",
          "stdio.py"
        ],
        "env": {
          "ctera.mcp.core.settings.scope": "user",
          "ctera.mcp.core.settings.host": "your.ctera.portal.domain",
          "ctera.mcp.core.settings.user": "your-username",
          "ctera.mcp.core.settings.password": "your-password"
        }
      }
    }
  }
```

Configuration using SSE:

```base
export ctera.mcp.core.settings.scope="user"
export ctera.mcp.core.settings.host="your.ctera.portal.domain"
export ctera.mcp.core.settings.user="your-username"
export ctera.mcp.core.settings.password="your-password"
```

```powershell
$env:ctera.mcp.core.settings.scope = "user"
$env:ctera.mcp.core.settings.host = "your.ctera.portal.domain"
$env:ctera.mcp.core.settings.user = "your-username"
$env:ctera.mcp.core.settings.password = "your-password"


```json
{
  "mcpServers": {
    "ctera-core-mcp-server-sse": {
      "url": "http://localhost:8000/sse"
    }
  }
}
