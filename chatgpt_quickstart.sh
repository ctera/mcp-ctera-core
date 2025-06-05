#!/bin/bash

echo "🤖 CTERA ChatGPT Integration - Quick Start"
echo "========================================"

# Check if servers are running
echo "🔍 Checking server status..."

# Test MCP Server
if curl -s http://localhost:8001/api/health >/dev/null 2>&1; then
    echo "✅ MCP Server (port 8001): Running"
else
    echo "❌ MCP Server (port 8001): Not running"
    echo "   Start with: python start_servers.py"
fi

# Test ChatGPT API
if curl -s http://localhost:8003/health >/dev/null 2>&1; then
    echo "✅ ChatGPT API (port 8003): Running"
else
    echo "❌ ChatGPT API (port 8003): Not running"
    echo "   Start with: python start_servers.py"
fi

echo ""
echo "🧪 Testing API endpoints..."

# Test who_am_i
echo -n "👤 Testing who_am_i: "
if curl -s -X POST http://localhost:8003/tools/who_am_i | grep -q "Authenticated"; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

# Test list_dir
echo -n "📁 Testing list_dir: "
if curl -s -X POST http://localhost:8003/tools/list_dir -H "Content-Type: application/json" -d '{"path":"/"}' | grep -q "result"; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

# Test ChatGPT OpenAPI endpoint
echo -n "📋 Testing ChatGPT OpenAPI: "
if curl -s http://localhost:8003/chatgpt-openapi.json | grep -q "CTERA Portal API"; then
    echo "✅ Working"
else
    echo "❌ Failed"
fi

echo ""
echo "🌐 Next Steps for ChatGPT Integration:"
echo "1. Install ngrok: brew install ngrok"
echo "2. Expose API: ngrok http 8003"
echo "3. Copy the ngrok URL (e.g., https://abc123.ngrok.io)"
echo "4. Go to ChatGPT and create a new GPT"
echo "5. In Actions, import: https://your-ngrok-url.ngrok.io/chatgpt-openapi.json"
echo ""
echo "📚 Full guide: See CHATGPT_SETUP_GUIDE.md" 