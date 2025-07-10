# Concurrent Chess

A modern chess application with AI and multiplayer support, featuring a concurrent chess engine and real-time WebSocket multiplayer.

## Features

### 🧠 AI Mode
- Play against a powerful concurrent chess engine
- Configurable AI difficulty levels (Easy, Medium, Hard)
- REST API-based communication for reliable gameplay

### 🌐 Multiplayer Mode
- Real-time multiplayer games using WebSocket connections
- Live game state synchronization
- Support for multiple concurrent games

### ⚡ Concurrent Engine
- Multi-threaded chess engine for fast AI moves
- Advanced evaluation function with piece-square tables
- Alpha-beta pruning with transposition tables

### 🎨 Modern Frontend
- React-based UI with TypeScript
- Beautiful, responsive design with Tailwind CSS
- Real-time move highlighting and legal move validation

## Architecture

```
ConcurrentChess/
├── backend/           # Python FastAPI backend
│   ├── main.py       # FastAPI server + WebSocket
│   ├── chess_engine.py # Concurrent chess engine
│   ├── chess_protocol.py # WebSocket message protocol
│   └── test_all.py   # Comprehensive tests
├── frontend/         # React TypeScript frontend
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/     # Page components
│   │   ├── services/  # API & WebSocket clients
│   │   └── types/     # TypeScript definitions
│   └── package.json
└── pieces/           # Chess piece images
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ConcurrentChess
```

2. **Set up the backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up the frontend**
```bash
cd ../frontend
npm install
```

### Running the Application

#### Option 1: Use the start script (Recommended)
```bash
./start.sh
```

#### Option 2: Start servers manually

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **WebSocket**: ws://localhost:8766

## Usage

### AI Mode
1. Navigate to "Play vs AI" from the home page
2. Choose your AI difficulty level
3. Play chess against the AI engine
4. The AI will automatically respond to your moves

### Multiplayer Mode
1. Navigate to "Multiplayer" from the home page
2. Choose your color (White or Black)
3. Play against another player in real-time
4. Both players see the same board state

## API Endpoints

### REST API (AI Mode)
- `GET /` - Server status
- `POST /api/games` - Create new game
- `GET /api/games/{game_id}` - Get game state
- `GET /api/games/{game_id}/legal_moves` - Get legal moves
- `POST /api/games/{game_id}/move` - Make a move
- `POST /api/games/{game_id}/ai_move` - Get AI move

### WebSocket Protocol (Multiplayer)
- `board_state` - Get current board state
- `legal_moves` - Get legal moves for current position
- `move` - Make a move
- `ai_move` - Get AI move (for testing)
- `evaluation` - Get position evaluation

## Development

### Backend Development
```bash
cd backend
# Run tests
python test_all.py

# Run individual tests
python test_client.py
```

### Frontend Development
```bash
cd frontend
# Start development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

## Testing

### Backend Tests
The backend includes comprehensive tests for both REST API and WebSocket functionality:

```bash
cd backend
python test_all.py
```

### Frontend Tests
The frontend uses TypeScript for type safety and includes ESLint for code quality.

## Performance

- **AI Engine**: Multi-threaded with parallel move evaluation
- **WebSocket**: Real-time communication with minimal latency
- **Frontend**: Optimized React components with efficient re-rendering

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License. 