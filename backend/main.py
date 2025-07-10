import threading
import socket
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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

# --- WebSocket Server (replaces TCP socket server) ---
SOCKET_HOST = '0.0.0.0'
SOCKET_PORT = 8766

# Global game state
_active_games = {}  # game_id -> Board

# --- Multiplayer Message Handlers (migrated from TCP socket server) ---
def handle_chess_message_ws(message: dict, websocket: WebSocket, addr=None) -> str:
    msg_type = message.get("type")
    if msg_type == MESSAGE_TYPES["MOVE"]:
        return handle_move_message(message)
    elif msg_type == MESSAGE_TYPES["BOARD_STATE"]:
        return handle_board_state_message(message)
    elif msg_type == MESSAGE_TYPES["LEGAL_MOVES"]:
        return handle_legal_moves_message(message)
    elif msg_type == MESSAGE_TYPES["EVALUATION"]:
        return handle_evaluation_message(message)
    elif msg_type == MESSAGE_TYPES["AI_MOVE"]:
        return handle_ai_move_message(message)
    else:
        return ChessProtocol.create_message(
            MESSAGE_TYPES["ERROR"],
            {"message": f"Unknown message type: {msg_type}"}
        )

def handle_move_message(message: dict) -> str:
    game_id = message.get("game_id", "default")
    move_data = message.get("move")
    if game_id not in _active_games:
        _active_games[game_id] = Board()
    board = _active_games[game_id]
    try:
        move = ChessProtocol.dict_to_move(move_data)
        legal_moves = list(board.legal_moves(board.turn))
        if move not in legal_moves:
            return ChessProtocol.create_message(
                MESSAGE_TYPES["ERROR"],
                {"message": "Illegal move"}
            )
        board._make_move(move)
        result = board.result()
        if result:
            return ChessProtocol.create_message(
                MESSAGE_TYPES["GAME_RESULT"],
                {"result": result, "board": ChessProtocol.board_to_dict(board)}
            )
        return ChessProtocol.create_message(
            MESSAGE_TYPES["BOARD_STATE"],
            {"board": ChessProtocol.board_to_dict(board)}
        )
    except Exception as e:
        return ChessProtocol.create_message(
            MESSAGE_TYPES["ERROR"],
            {"message": f"Error processing move: {str(e)}"}
        )

def handle_board_state_message(message: dict) -> str:
    game_id = message.get("game_id", "default")
    if game_id not in _active_games:
        _active_games[game_id] = Board()
    board = _active_games[game_id]
    return ChessProtocol.create_message(
        MESSAGE_TYPES["BOARD_STATE"],
        {"board": ChessProtocol.board_to_dict(board)}
    )

def handle_legal_moves_message(message: dict) -> str:
    game_id = message.get("game_id", "default")
    if game_id not in _active_games:
        _active_games[game_id] = Board()
    board = _active_games[game_id]
    moves = list(board.legal_moves(board.turn))
    moves_dict = [ChessProtocol.move_to_dict(m) for m in moves]
    return ChessProtocol.create_message(
        MESSAGE_TYPES["LEGAL_MOVES"],
        {"moves": moves_dict}
    )

def handle_evaluation_message(message: dict) -> str:
    game_id = message.get("game_id", "default")
    if game_id not in _active_games:
        _active_games[game_id] = Board()
    board = _active_games[game_id]
    from chess_engine import evaluate_board
    eval_score = evaluate_board(board, Color.WHITE)
    return ChessProtocol.create_message(
        MESSAGE_TYPES["EVALUATION"],
        {"evaluation": eval_score / 100.0}
    )

def handle_ai_move_message(message: dict) -> str:
    game_id = message.get("game_id", "default")
    depth = message.get("depth", 4)
    if game_id not in _active_games:
        _active_games[game_id] = Board()
    board = _active_games[game_id]
    from chess_engine import find_best_move_parallel
    try:
        ai_move = find_best_move_parallel(board, board.turn, depth)
        if ai_move:
            board._make_move(ai_move)
            result = board.result()
            if result:
                return ChessProtocol.create_message(
                    MESSAGE_TYPES["GAME_RESULT"],
                    {"result": result, "board": ChessProtocol.board_to_dict(board)}
                )
            return ChessProtocol.create_message(
                MESSAGE_TYPES["AI_MOVE"],
                {
                    "move": ChessProtocol.move_to_dict(ai_move),
                    "board": ChessProtocol.board_to_dict(board)
                }
            )
        else:
            return ChessProtocol.create_message(
                MESSAGE_TYPES["ERROR"],
                {"message": "No legal moves available"}
            )
    except Exception as e:
        return ChessProtocol.create_message(
            MESSAGE_TYPES["ERROR"],
            {"message": f"Error calculating AI move: {str(e)}"}
        )

# --- WebSocket endpoint ---
from starlette.websockets import WebSocketState

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_addr = websocket.client.host if websocket.client else None
    try:
        while True:
            data = await websocket.receive_text()
            message = ChessProtocol.parse_message(data)
            if not message:
                error_msg = ChessProtocol.create_message(
                    MESSAGE_TYPES["ERROR"],
                    {"message": "Invalid JSON message"}
                )
                await websocket.send_text(error_msg)
                continue
            response = handle_chess_message_ws(message, websocket, client_addr)
            if response and websocket.application_state == WebSocketState.CONNECTED:
                await websocket.send_text(response)
    except WebSocketDisconnect:
        print(f"[WebSocket] Disconnected: {client_addr}")
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        if websocket.application_state == WebSocketState.CONNECTED:
            error_msg = ChessProtocol.create_message(
                MESSAGE_TYPES["ERROR"],
                {"message": f"Server error: {str(e)}"}
            )
            await websocket.send_text(error_msg)

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

if __name__ == "__main__":
    uvicorn.run("main:app", host=SOCKET_HOST, port=SOCKET_PORT, reload=False) 