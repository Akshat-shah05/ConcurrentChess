import threading
import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import atexit
from chess_engine import Board, Color
from chess_protocol import ChessProtocol, MESSAGE_TYPES

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SOCKET_HOST = '0.0.0.0'
SOCKET_PORT = 8000

# Global game state
_active_games = {}  # game_id -> Board

@app.get("/")
def root():
    return {"status": "FastAPI backend running", "socket_port": SOCKET_PORT}

@app.get("/api/games")
def list_games():
    """List all active games."""
    return {"games": list(_active_games.keys())}

@app.post("/api/games")
def create_game():
    """Create a new game."""
    import uuid
    game_id = str(uuid.uuid4())
    _active_games[game_id] = Board()
    return {"game_id": game_id, "status": "created"}

@app.get("/api/games/{game_id}")
def get_game_state(game_id: str):
    """Get the current state of a game."""
    if game_id not in _active_games:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Game not found")
    board = _active_games[game_id]
    return {
        "game_id": game_id,
        "board": ChessProtocol.board_to_dict(board),
        "result": board.result()
    }

@app.post("/api/games/{game_id}/move")
def make_move(game_id: str, move_data: dict):
    """Make a move in a game."""
    if game_id not in _active_games:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Game not found")
    board = _active_games[game_id]
    try:
        move = ChessProtocol.dict_to_move(move_data)
        legal_moves = list(board.legal_moves(board.turn))
        if move not in legal_moves:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Illegal move")
        board._make_move(move)
        result = board.result()
        return {
            "game_id": game_id,
            "board": ChessProtocol.board_to_dict(board),
            "result": result
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Error processing move: {str(e)}")

@app.post("/api/games/{game_id}/ai_move")
def get_ai_move(game_id: str, depth: int = 4):
    """Get an AI move for the current position."""
    if game_id not in _active_games:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Game not found")
    board = _active_games[game_id]
    from chess_engine import find_best_move_parallel
    try:
        ai_move = find_best_move_parallel(board, board.turn, depth)
        if ai_move:
            board._make_move(ai_move)
            result = board.result()
            return {
                "game_id": game_id,
                "move": ChessProtocol.move_to_dict(ai_move),
                "board": ChessProtocol.board_to_dict(board),
                "result": result
            }
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="No legal moves available")
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Error calculating AI move: {str(e)}")

@app.get("/api/games/{game_id}/legal_moves")
def get_legal_moves(game_id: str):
    """Get legal moves for the current position."""
    if game_id not in _active_games:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Game not found")
    board = _active_games[game_id]
    legal_moves = list(board.legal_moves(board.turn))
    return {
        "game_id": game_id,
        "moves": [ChessProtocol.move_to_dict(move) for move in legal_moves]
    }

@app.get("/api/games/{game_id}/evaluation")
def get_evaluation(game_id: str):
    """Get the current board evaluation."""
    if game_id not in _active_games:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Game not found")
    board = _active_games[game_id]
    from chess_engine import evaluate_board
    eval_score = evaluate_board(board, Color.WHITE)
    return {
        "game_id": game_id,
        "evaluation": eval_score / 100.0  # Convert to pawns
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host=SOCKET_HOST, port=SOCKET_PORT, reload=False) 