#!/bin/bash

echo "================================================"
echo "  Agentic RAG — Backend Server"
echo "================================================"
echo ""
echo "Note: The Mock MCP Server starts automatically"
echo "via stdio when the Agent requests external rules."
echo ""

cd "$(dirname "$0")/backend" || exit 1
source venv/bin/activate
uvicorn main:app --port 8000 --reload
