#!/bin/bash

# TerraWatch Startup Script
# Starts both backend and frontend services

echo "🚀 Starting TerraWatch..."

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill 0
}
trap cleanup EXIT

# Start backend in background
echo "📡 Starting backend server on port 8001..."
cd backend
PYTHONPATH=/Users/dhanshri/Documents/hackathon/terrawatch python3 main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend in background
echo "🌐 Starting frontend development server on port 3000..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ Services starting up..."
echo "📡 Backend: http://localhost:8001"
echo "🌐 Frontend: http://localhost:3000"
echo "📊 API Docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait