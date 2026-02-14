#!/bin/bash

# Quick start script for TestAIAgent

echo "Starting TestAIAgent..."

# Check if config.yaml exists
if [ ! -f config.yaml ]; then
    echo "Error: config.yaml not found!"
    echo "Please copy config.yaml.example to config.yaml and add your API keys"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install backend dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing backend dependencies..."
    pip install -e ".[web]"
fi

# Check if frontend dependencies are installed
if [ ! -d frontend/node_modules ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start backend in background
echo "Starting backend on http://localhost:8000..."
uvicorn web.main:app --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend on http://localhost:5173..."
cd frontend
npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
