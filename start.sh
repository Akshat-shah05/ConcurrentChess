#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Concurrent Chess - AI & Multiplayer Mode${NC}"
echo "=================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python is installed
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js and try again."
    exit 1
fi

# Check if npm is installed
if ! command_exists npm; then
    print_error "npm is not installed. Please install npm and try again."
    exit 1
fi

print_status "Checking dependencies..."

# Setup Python virtual environment
if [ ! -d "venv" ]; then
    print_warning "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Install frontend dependencies
print_status "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Function to start backend servers
start_backend() {
    echo -e "${BLUE}🔧 Starting Backend Servers...${NC}"
    
    # Start REST API backend for AI mode
    echo -e "${GREEN}Starting REST API backend on http://localhost:8000${NC}"
    (cd backend && source ../venv/bin/activate && python -m uvicorn main:app --host 0.0.0.0 --port 8000) &
    REST_PID=$!
    
    # Wait a moment for REST server to start
    sleep 2
    
    # Start WebSocket backend for multiplayer mode
    echo -e "${GREEN}Starting WebSocket backend on ws://localhost:8766${NC}"
    (cd backend && source ../venv/bin/activate && python -m uvicorn websocket_server:app --host 0.0.0.0 --port 8766) &
    WS_PID=$!
    
    # Wait a moment for WebSocket server to start
    sleep 2
    
    # Check if servers started successfully
    if curl -s http://localhost:8000 > /dev/null; then
        print_status "REST API server is running on http://localhost:8000"
    else
        print_error "Failed to start REST API server"
        return 1
    fi
    
    if curl -s http://localhost:8766 > /dev/null 2>&1; then
        print_status "WebSocket server is running on ws://localhost:8766"
    else
        print_warning "WebSocket server might still be starting..."
    fi
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}🎨 Starting Frontend...${NC}"
    
    # Start frontend dev server
    echo -e "${GREEN}Starting frontend dev server...${NC}"
    (cd frontend && npm run dev) &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    sleep 5
    
    # Try to detect the frontend URL
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        FRONTEND_URL="http://localhost:3000"
    elif curl -s http://localhost:3001 > /dev/null 2>&1; then
        FRONTEND_URL="http://localhost:3001"
    elif curl -s http://localhost:5173 > /dev/null 2>&1; then
        FRONTEND_URL="http://localhost:5173"
    else
        FRONTEND_URL="http://localhost:3000 (or check terminal for actual port)"
    fi
    
    print_status "Frontend is running on $FRONTEND_URL"
}

# Function to show status
show_status() {
    echo ""
    echo -e "${BLUE}📊 Server Status:${NC}"
    echo "=================================================="
    
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ REST API (AI Mode): http://localhost:8000${NC}"
    else
        echo -e "${RED}❌ REST API (AI Mode): Not running${NC}"
    fi
    
    if curl -s http://localhost:8766 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ WebSocket (Multiplayer): ws://localhost:8766${NC}"
    else
        echo -e "${RED}❌ WebSocket (Multiplayer): Not running${NC}"
    fi
    
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend: http://localhost:3000${NC}"
    elif curl -s http://localhost:3001 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend: http://localhost:3001${NC}"
    elif curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend: http://localhost:5173${NC}"
    else
        echo -e "${RED}❌ Frontend: Not running${NC}"
    fi
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down servers...${NC}"
    kill $REST_PID $WS_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start all services
echo ""
start_backend
if [ $? -ne 0 ]; then
    print_error "Failed to start backend servers"
    exit 1
fi

start_frontend

# Show final status
show_status

echo ""
echo -e "${BLUE}🎮 Concurrent Chess is ready!${NC}"
echo "=================================================="
echo -e "${GREEN}🎯 AI Mode:${NC} Play against the chess AI"
echo -e "${GREEN}👥 Multiplayer Mode:${NC} Play against other players"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "- Open the frontend URL in your browser"
echo "- Click 'Play vs AI' for AI mode"
echo "- Click 'Multiplayer' for multiplayer mode"
echo "- Create or join games in multiplayer mode"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"

# Wait for all processes
wait $REST_PID $WS_PID $FRONTEND_PID 