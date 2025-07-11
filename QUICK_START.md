# 🎮 Concurrent Chess - Quick Start Guide

## 🚀 Get Started in 2 Minutes

### First Time Setup
```bash
# 1. Clone the repository
git clone <repository-url>
cd ConcurrentChess

# 2. Run setup (installs all dependencies)
./setup.sh

# 3. Start the application
./start.sh
```

### Regular Usage
```bash
# Start the application
./start.sh

# Check if everything is running
./status.sh

# Stop all services
./stop.sh
```

## 🎯 What You Get

### ✅ AI Mode
- Play against a powerful chess AI
- Multiple difficulty levels
- REST API backend for reliable gameplay

### ✅ Multiplayer Mode  
- Real-time multiplayer games
- Game lobby with create/join functionality
- WebSocket backend for live synchronization

### ✅ Modern UI
- Beautiful, responsive design
- Real-time move highlighting
- Legal move validation

## 🌐 Access URLs

Once started, you can access:
- **Frontend**: http://localhost:3000 (or check terminal for actual port)
- **REST API (AI Mode)**: http://localhost:8000
- **WebSocket (Multiplayer)**: ws://localhost:8766

## 🎮 How to Play

### AI Mode
1. Open the frontend URL in your browser
2. Click "Play vs AI"
3. Choose difficulty level
4. Start playing!

### Multiplayer Mode
1. Open the frontend URL in your browser
2. Click "Multiplayer"
3. **Create a Game**: Click "Create Game" to start a new game
4. **Join a Game**: Browse available games and click "Join"
5. Wait for opponent to join
6. Play chess in real-time!

## 🛠️ Scripts Overview

| Script | Purpose |
|--------|---------|
| `./setup.sh` | Install all dependencies (first time only) |
| `./start.sh` | Start all services (AI + Multiplayer) |
| `./status.sh` | Check if all services are running |
| `./stop.sh` | Stop all services |

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
./setup.sh
```

### "Port already in use"
The start script will automatically find available ports. Check terminal output for actual URLs.

### "Frontend not loading"
```bash
cd frontend && npm install
```

### Check if everything is working
```bash
./status.sh
```

## 📊 System Requirements

- **Python 3.8+**
- **Node.js 16+**
- **npm**

The setup script will check these automatically.

## 🎉 Ready to Play!

Your Concurrent Chess application is now ready with both AI and multiplayer modes working perfectly!

- **AI Mode**: Challenge the chess engine
- **Multiplayer Mode**: Play against friends in real-time
- **Modern UI**: Beautiful, responsive interface

Happy chess playing! 🎮♟️ 