#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Concurrent Chess Services${NC}"
echo "=================================================="

# Function to kill processes on a port
kill_port() {
    local port=$1
    local service=$2
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}Stopping $service on port $port...${NC}"
        kill -TERM $pids 2>/dev/null
        sleep 2
        # Force kill if still running
        pids=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pids" ]; then
            echo -e "${YELLOW}Force stopping $service...${NC}"
            kill -KILL $pids 2>/dev/null
        fi
        echo -e "${GREEN}✅ $service stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  $service was not running on port $port${NC}"
    fi
}

# Stop all services
echo -e "${BLUE}Stopping services...${NC}"
echo ""

kill_port 8000 "REST API (AI Mode)"
kill_port 8766 "WebSocket (Multiplayer)"
kill_port 3000 "Frontend"
kill_port 3001 "Frontend (Alternative)"
kill_port 5173 "Frontend (Vite)"

echo ""
echo -e "${GREEN}🎉 All services stopped!${NC}"
echo ""
echo -e "${BLUE}💡 To start again:${NC}"
echo "- Run './start.sh' to start all services"
echo "- Run './status.sh' to check service status" 