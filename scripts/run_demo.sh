#!/bin/bash
# UCP Demo Run Script - Starts both backend and frontend

set -e

PROJECT_DIR="$(dirname "$0")/.."
cd "$PROJECT_DIR"

echo "============================================"
echo "         UCP Demo - Starting Up"
echo "============================================"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Start backend
echo "Starting backend server..."
poetry run python -m backend.main &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 3

# Start frontend
echo "Starting frontend dev server..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "============================================"
echo "         UCP Demo is running!"
echo "============================================"
echo ""
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Discovery: http://localhost:8000/.well-known/ucp"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
