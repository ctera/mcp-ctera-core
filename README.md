# MCP Server for CTERA

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

Example configuration snippet for `mcp.json`:

```json
{
  "mcpServers": {
    "ctera": {
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/mcp-server-ctera/src",
        "run",
        "mcp_ctera.py"
      ],
      "env": {
        "CTERA_ADDR": "portal.ctera.com",
        "CTERA_USER": "username",
        "CTERA_PASS": "password"
      }
    }
  }
}
