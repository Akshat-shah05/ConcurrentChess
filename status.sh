#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 Concurrent Chess Status Check${NC}"
echo "=================================================="

# Function to check if a port is in use
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $service is running on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service is not running on port $port${NC}"
        return 1
    fi
}

# Check all services
echo -e "${BLUE}Checking services...${NC}"
echo ""

REST_RUNNING=false
WS_RUNNING=false
FRONTEND_RUNNING=false

# Check REST API
if check_port 8000 "REST API (AI Mode)"; then
    REST_RUNNING=true
fi

# Check WebSocket server
if check_port 8766 "WebSocket (Multiplayer)"; then
    WS_RUNNING=true
fi

# Check frontend (common ports)
if check_port 3000 "Frontend" || check_port 3001 "Frontend" || check_port 5173 "Frontend"; then
    FRONTEND_RUNNING=true
fi

echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "=================================================="

if [ "$REST_RUNNING" = true ] && [ "$WS_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
    echo -e "${GREEN}🎉 All services are running!${NC}"
    echo ""
    echo -e "${YELLOW}Access URLs:${NC}"
    echo "- Frontend: http://localhost:3000 (or check for actual port)"
    echo "- REST API: http://localhost:8000"
    echo "- WebSocket: ws://localhost:8766"
    echo ""
    echo -e "${GREEN}Ready to play chess! 🎮${NC}"
elif [ "$REST_RUNNING" = true ] && [ "$WS_RUNNING" = true ]; then
    echo -e "${YELLOW}⚠️  Backend services are running, but frontend might not be ready yet${NC}"
    echo "Try refreshing the page or wait a moment"
elif [ "$REST_RUNNING" = true ]; then
    echo -e "${YELLOW}⚠️  Only REST API is running${NC}"
    echo "Run './start.sh' to start all services"
else
    echo -e "${RED}❌ No services are running${NC}"
    echo "Run './start.sh' to start the application"
fi

echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo "- Run './start.sh' to start all services"
echo "- Run './setup.sh' if you need to install dependencies"
echo "- Check the terminal where you ran './start.sh' for detailed logs" 