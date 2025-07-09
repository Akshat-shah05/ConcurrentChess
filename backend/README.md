# ConcurrentChess Backend

This backend uses [FastAPI](https://fastapi.tiangolo.com/) for HTTP endpoints and a TCP/IP socket server for real-time chess communication.

## Structure
- `main.py`: FastAPI app and background TCP socket server
- `chess_engine.py`: Core chess logic extracted from the original GUI
- `chess_protocol.py`: Chess protocol message handling
- `test_client.py`: Simple test client for TCP socket communication
- `requirements.txt`: Python dependencies

## Running the Backend

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the backend:
   ```bash
   python main.py
   ```
   - FastAPI will run on [http://localhost:8000](http://localhost:8000)
   - The TCP socket server will listen on port 8766

## API Endpoints

### REST API (HTTP)
- `GET /api/games` - List all active games
- `POST /api/games` - Create a new game
- `GET /api/games/{game_id}` - Get game state
- `POST /api/games/{game_id}/move` - Make a move
- `GET /api/games/{game_id}/legal_moves` - Get legal moves
- `POST /api/games/{game_id}/ai_move` - Get AI move

### TCP Socket Protocol
The socket server accepts JSON messages with the following types:
- `board_state` - Get current board state
- `legal_moves` - Get legal moves for current position
- `move` - Make a move
- `ai_move` - Get AI move
- `evaluation` - Get position evaluation

## Testing

Run the test client to verify functionality:
```bash
python test_client.py
```

## Next Steps
- Add WebSocket support for real-time updates
- Implement multiplayer game management
- Add user authentication and game persistence 