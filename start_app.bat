@echo off
echo ========================================================
echo Starting Agentic RAG Invoice Validation System
echo ========================================================
echo.
echo - Note: The Mock MCP Server runs dynamically in the background via Standard I/O (stdio) when the Agent requests external validation rules.

echo Launching Backend Server...
start "Agentic RAG Backend (FastAPI)" cmd /k "cd backend && venv\Scripts\activate.bat && uvicorn main:app --port 8000"

echo Launching Frontend Development Server...
start "Agentic RAG Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo All servers have been launched in separate windows!
echo - Keep those windows open while using the app.
echo.
echo -^> The Frontend UI will be available at: http://localhost:5173
echo -^> The Backend API is running on: http://localhost:8000
echo.
pause
