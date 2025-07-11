#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Concurrent Chess Setup${NC}"
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

# Check system requirements
echo -e "${BLUE}Checking system requirements...${NC}"

# Check Python
if ! command_exists python3; then
    print_error "Python 3 is not installed."
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
else
    print_status "Python 3 is installed"
fi

# Check Node.js
if ! command_exists node; then
    print_error "Node.js is not installed."
    echo "Please install Node.js from https://nodejs.org"
    exit 1
else
    print_status "Node.js is installed"
fi

# Check npm
if ! command_exists npm; then
    print_error "npm is not installed."
    echo "Please install npm (usually comes with Node.js)"
    exit 1
else
    print_status "npm is installed"
fi

echo ""
echo -e "${BLUE}Setting up Python environment...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_warning "Creating Python virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r backend/requirements.txt

echo ""
echo -e "${BLUE}Setting up frontend...${NC}"

# Install frontend dependencies
print_status "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo -e "${BLUE}🎉 Setup Complete!${NC}"
echo "=================================================="
print_status "All dependencies are installed"
print_status "Python virtual environment is ready"
print_status "Frontend dependencies are installed"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run './start.sh' to start the application"
echo "2. Open your browser to the frontend URL"
echo "3. Enjoy playing chess!"
echo ""
echo -e "${GREEN}Happy chess playing! 🎮${NC}" 