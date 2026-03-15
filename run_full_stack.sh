#!/bin/bash

# TerraWatch Full Stack Startup Script
# Runs both Backend (FastAPI) and Frontend (React)

set -e

PROJECT_DIR="/Users/sameeksha/Documents/Career/hackthon/girls_in_code/terrawatch"

echo "🚀 Starting TerraWatch Full Stack..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    # Kill all background processes
    jobs -p | xargs kill 2>/dev/null || true
    exit 0
}

trap cleanup EXIT INT TERM

cd "$PROJECT_DIR"

# ============================================================
# Start Backend
# ============================================================
echo "📡 Starting Backend (FastAPI) on http://localhost:8001..."
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
source ./venv/bin/activate

# Start backend in background
cd backend
python3 main.py > /tmp/terrawatch-backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check logs:"
    cat /tmp/terrawatch-backend.log
    exit 1
fi

# ============================================================
# Start Frontend
# ============================================================
echo ""
echo "🌐 Starting Frontend (React) on http://localhost:3000..."

cd frontend

# Start frontend in background
BROWSER=none npm start > /tmp/terrawatch-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

# ============================================================
# Display Info
# ============================================================
echo ""
echo "════════════════════════════════════════════════════════"
echo "✨ TerraWatch is now running! ✨"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📡 Backend API:        http://localhost:8001"
echo "📊 API Docs (Swagger): http://localhost:8001/docs"
echo "🌐 Frontend App:       http://localhost:3000"
echo ""
echo "════════════════════════════════════════════════════════"
echo ""
echo "🎯 What to do:"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Search for cities and explore climate risks"
echo "  3. View AI-powered risk analysis"
echo "  4. Check insurance premiums"
echo ""
echo "🔧 Developer tools:"
echo "  - API Docs: http://localhost:8001/docs"
echo "  - Backend logs: tail -f /tmp/terrawatch-backend.log"
echo "  - Frontend logs: tail -f /tmp/terrawatch-frontend.log"
echo ""
echo "🛑 To stop: Press Ctrl+C"
echo ""
echo "════════════════════════════════════════════════════════"
echo ""

# Wait for both processes
wait
