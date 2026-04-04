#!/bin/bash

echo "================================================"
echo "  Agentic RAG — Frontend Dev Server"
echo "================================================"
echo ""

cd "$(dirname "$0")/frontend" || exit 1
npm run dev
