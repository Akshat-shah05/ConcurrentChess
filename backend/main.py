import threading
import socket
from fastapi import FastAPI
import uvicorn
import atexit
from chess_engine import Board, Color
from chess_protocol import ChessProtocol, MESSAGE_TYPES

app = FastAPI()

# --- TCP/IP Socket Server (runs in background) ---
SOCKET_HOST = '0.0.0.0'
SOCKET_PORT = 8766

# Global socket server state
_socket_server = None
_socket_thread = None

# Global game state
_active_games = {}  # game_id -> Board

def handle_client(conn, addr):
    print(f"[SOCKET] Connection from {addr}")
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            
            message = data.decode('utf-8').strip()
            if not message:
                continue
            
            print(f"[SOCKET] Received: {message}")
                
            # Parse and handle chess protocol message
            parsed = ChessProtocol.parse_message(message)
            if parsed:
                print(f"[SOCKET] Parsed message type: {parsed.get('type')}")
                response = handle_chess_message(parsed, addr)
                if response:
                    print(f"[SOCKET] Sending response: {response.strip()}")
                    conn.sendall(response.encode('utf-8'))
            else:
                print(f"[SOCKET] Failed to parse message")
                # Send error for invalid JSON
                error_msg = ChessProtocol.create_message(
                    MESSAGE_TYPES["ERROR"], 
                    {"message": "Invalid JSON message"}
                )
                conn.sendall(error_msg.encode('utf-8'))
                
    except Exception as e:
        print(f"[SOCKET] Error: {e}")
    finally:
        conn.close()
        print(f"[SOCKET] Closed connection from {addr}")

def handle_chess_message(message: dict, addr) -> str:
    """Handle chess protocol messages and return response."""
    msg_type = message.get("type")
    print(f"[SOCKET] Handling message type: {msg_type}")
    print(f"[SOCKET] Available message types: {list(MESSAGE_TYPES.values())}")
    
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
        print(f"[SOCKET] Unknown message type: {msg_type}")
        return ChessProtocol.create_message(
            MESSAGE_TYPES["ERROR"],
            {"message": f"Unknown message type: {msg_type}"}
        )

def handle_move_message(message: dict) -> str:
    """Handle a move message."""
    game_id = message.get("game_id", "default")
    move_data = message.get("move")
    
    if game_id not in _active_games:
        _active_games[game_id] = Board()
    
    board = _active_games[game_id]
    
    try:
        move = ChessProtocol.dict_to_move(move_data)
        # Check if move is legal
        legal_moves = list(board.legal_moves(board.turn))
        if move not in legal_moves:
            return ChessProtocol.create_message(
                MESSAGE_TYPES["ERROR"],
                {"message": "Illegal move"}
            )
        
        # Make the move
        board._make_move(move)
        
        # Check for game result
        result = board.result()
        if result:
            return ChessProtocol.create_message(
                MESSAGE_TYPES["GAME_RESULT"],
                {"result": result, "board": ChessProtocol.board_to_dict(board)}
            )
        
        # Return updated board state
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
    """Handle a board state request."""
    game_id = message.get("game_id", "default")
    
    if game_id not in _active_games:
        _active_games[game_id] = Board()
    
    board = _active_games[game_id]
    return ChessProtocol.create_message(
        MESSAGE_TYPES["BOARD_STATE"],
        {"board": ChessProtocol.board_to_dict(board)}
    )

def handle_legal_moves_message(message: dict) -> str:
    """Handle a legal moves request."""
    game_id = message.get("game_id", "default")
    
    if game_id not in _active_games:
        _active_games[game_id] = Board()
    
    board = _active_games[game_id]
    legal_moves = list(board.legal_moves(board.turn))
    
    moves_data = [ChessProtocol.move_to_dict(move) for move in legal_moves]
    return ChessProtocol.create_message(
        MESSAGE_TYPES["LEGAL_MOVES"],
        {"moves": moves_data}
    )

def handle_evaluation_message(message: dict) -> str:
    """Handle an evaluation request."""
    game_id = message.get("game_id", "default")
    
    if game_id not in _active_games:
        _active_games[game_id] = Board()
    
    board = _active_games[game_id]
    from chess_engine import evaluate_board
    
    eval_score = evaluate_board(board, Color.WHITE)
    return ChessProtocol.create_message(
        MESSAGE_TYPES["EVALUATION"],
        {"evaluation": eval_score / 100.0}  # Convert to pawns
    )

def handle_ai_move_message(message: dict) -> str:
    """Handle an AI move request."""
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

def socket_server():
    global _socket_server
    try:
        _socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _socket_server.bind((SOCKET_HOST, SOCKET_PORT))
        _socket_server.listen()
        print(f"[SOCKET] Listening on {SOCKET_HOST}:{SOCKET_PORT}")
        while True:
            conn, addr = _socket_server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"[SOCKET] Port {SOCKET_PORT} already in use, skipping socket server")
        else:
            raise
    except Exception as e:
        print(f"[SOCKET] Error: {e}")

def cleanup_socket():
    global _socket_server
    if _socket_server:
        _socket_server.close()
        print("[SOCKET] Cleaned up socket server")

# Register cleanup
atexit.register(cleanup_socket)

# Start socket server in background (only in main process)
if __name__ == "__main__":
    _socket_thread = threading.Thread(target=socket_server, daemon=True)
    _socket_thread.start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
else:
    # When imported as module (e.g., by uvicorn), don't start socket server
    pass

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
        return {"error": "Game not found"}, 404
    
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
        return {"error": "Game not found"}, 404
    
    board = _active_games[game_id]
    
    try:
        move = ChessProtocol.dict_to_move(move_data)
        legal_moves = list(board.legal_moves(board.turn))
        
        if move not in legal_moves:
            return {"error": "Illegal move"}, 400
        
        board._make_move(move)
        result = board.result()
        
        return {
            "game_id": game_id,
            "board": ChessProtocol.board_to_dict(board),
            "result": result
        }
    except Exception as e:
        return {"error": f"Error processing move: {str(e)}"}, 400

@app.get("/api/games/{game_id}/legal_moves")
def get_legal_moves(game_id: str):
    """Get legal moves for the current position."""
    if game_id not in _active_games:
        return {"error": "Game not found"}, 404
    
    board = _active_games[game_id]
    legal_moves = list(board.legal_moves(board.turn))
    
    return {
        "game_id": game_id,
        "moves": [ChessProtocol.move_to_dict(move) for move in legal_moves]
    }

@app.post("/api/games/{game_id}/ai_move")
def get_ai_move(game_id: str, depth: int = 4):
    """Get an AI move for the current position."""
    if game_id not in _active_games:
        return {"error": "Game not found"}, 404
    
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
            return {"error": "No legal moves available"}, 400
    except Exception as e:
        return {"error": f"Error calculating AI move: {str(e)}"}, 500 