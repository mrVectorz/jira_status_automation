#!/bin/bash

# Jira Status Automation - Quick Start Script
# This script helps you get the application running quickly

set -e

# Default configuration (can be overridden by environment variables)
export BACKEND_HOST=${BACKEND_HOST:-"0.0.0.0"}
export BACKEND_PORT=${BACKEND_PORT:-8000}
export FRONTEND_HOST=${FRONTEND_HOST:-"localhost"}
export FRONTEND_PORT=${FRONTEND_PORT:-3001}

echo "🚀 Jira Status Automation - Quick Start"
echo "======================================"
echo "Backend will run on:  http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "Frontend will run on: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo ""
echo "To customize ports, set environment variables:"
echo "  BACKEND_PORT=8001 FRONTEND_PORT=3002 ./start.sh"
echo "======================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "Please install Node.js 16+ and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo "✅ Node.js found: $(node --version)"

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Check for virtual environment and create if needed
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
if ! ./venv/bin/pip install -r requirements.txt; then
    echo "❌ Failed to install Python dependencies"
    echo "Try manually: ./venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Install frontend dependencies
echo ""
echo "📦 Installing frontend dependencies..."
cd frontend
if ! npm install; then
    echo "❌ Failed to install frontend dependencies"
    echo "Please check your Node.js installation and try again"
    exit 1
fi
cd ..

echo ""
echo "✅ All dependencies installed successfully!"

# Test the API
echo ""
echo "🧪 Testing API functionality..."
if python3 test_api.py; then
    echo "✅ API tests passed!"
else
    echo "⚠️  Some API tests failed, but the application should still work"
fi

echo ""
echo "🎉 Setup complete! Starting the application..."
echo ""

# Start backend in background
echo "Starting backend server..."
./venv/bin/python run_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "Starting frontend server..."
cd frontend

# Set frontend environment variables
export PORT=${FRONTEND_PORT}
export REACT_APP_API_URL="http://localhost:${BACKEND_PORT}"

npm start &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

echo ""
echo "🌟 Application is starting up!"
echo ""
echo "Backend API: http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "API Docs: http://${BACKEND_HOST}:${BACKEND_PORT}/docs"
echo "Frontend: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo ""
echo "The application should open automatically in your browser."
echo ""
echo "Configuration:"
echo "  Backend Host: ${BACKEND_HOST}"
echo "  Backend Port: ${BACKEND_PORT}"
echo "  Frontend Host: ${FRONTEND_HOST}"
echo "  Frontend Port: ${FRONTEND_PORT}"
echo ""
echo "To stop the application:"
echo "  - Press Ctrl+C to stop this script"
echo "  - Or run: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Wait for user to stop
wait
