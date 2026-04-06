#!/bin/bash

echo "========================================================"
echo "Starting Agentic RAG Invoice Validation System"
echo "========================================================"
echo ""
echo "- Note: The Mock MCP Server runs dynamically in the background via Standard I/O (stdio) when the Agent requests external validation rules."
echo ""

# Start the frontend in a background process
echo "Launching Frontend Development Server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Start the backend in the foreground
echo "Launching Backend Server..."
cd backend
source venv/bin/activate
uvicorn main:app --port 8000

# Cleanup on exit
trap "kill $FRONTEND_PID" EXIT
