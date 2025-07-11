import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from chess_engine import Board, Color
from chess_protocol import ChessProtocol, MESSAGE_TYPES
import uuid
from typing import Dict, Set, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SOCKET_HOST = '0.0.0.0'
SOCKET_PORT = 8766

# Game management
_active_games: Dict[str, Board] = {}  # game_id -> Board
connections: Dict[str, Set[WebSocket]] = {}  # game_id -> set of WebSocket
player_colors: Dict[WebSocket, str] = {}  # WebSocket -> color
game_players: Dict[str, Dict[str, WebSocket]] = {}  # game_id -> {color: websocket}
available_games: Dict[str, Dict] = {}  # game_id -> game info

async def broadcast(game_id: str, message: str, exclude: Optional[WebSocket] = None):
    """Broadcast message to all players in a game."""
    if game_id in connections:
        for ws in connections[game_id]:
            if ws != exclude:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass

async def broadcast_game_list():
    """Broadcast updated game list to all connected clients."""
    game_list = []
    for game_id, game_info in available_games.items():
        if game_id in _active_games:
            game_list.append({
                "game_id": game_id,
                "players": len(connections.get(game_id, set())),
                "max_players": 2,
                "status": "waiting" if len(connections.get(game_id, set())) < 2 else "playing"
            })
    
    message = ChessProtocol.create_message("game_list", {"games": game_list})
    # Broadcast to all connected clients
    for game_connections in connections.values():
        for ws in game_connections:
            try:
                await ws.send_text(message)
            except Exception:
                pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    game_id = None
    player_color = None
    
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
                
            msg_type = message.get("type")
            
            if msg_type == "create_game":
                # Create a new game
                new_game_id = str(uuid.uuid4())[:8]
                _active_games[new_game_id] = Board()
                connections[new_game_id] = set()
                game_players[new_game_id] = {}
                available_games[new_game_id] = {
                    "game_id": new_game_id,
                    "created_at": "now",
                    "status": "waiting"
                }
                
                await websocket.send_text(ChessProtocol.create_message(
                    "game_created", 
                    {"game_id": new_game_id}
                ))
                
                await broadcast_game_list()
                
            elif msg_type == "get_games":
                # Send list of available games
                game_list = []
                for gid, game_info in available_games.items():
                    if gid in _active_games:
                        game_list.append({
                            "game_id": gid,
                            "players": len(connections.get(gid, set())),
                            "max_players": 2,
                            "status": "waiting" if len(connections.get(gid, set())) < 2 else "playing"
                        })
                
                await websocket.send_text(ChessProtocol.create_message(
                    "game_list", 
                    {"games": game_list}
                ))
                
            elif msg_type == "join":
                game_id = message.get("game_id")
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(
                        MESSAGE_TYPES["ERROR"], 
                        {"message": "Missing game_id in join"}
                    ))
                    continue
                    
                if game_id not in _active_games:
                    await websocket.send_text(ChessProtocol.create_message(
                        MESSAGE_TYPES["ERROR"], 
                        {"message": "Game not found"}
                    ))
                    continue
                    
                # Add player to game
                connections[game_id].add(websocket)
                
                # Assign color
                if Color.WHITE not in [player_colors.get(ws) for ws in connections[game_id]]:
                    player_colors[websocket] = "white"
                    player_color = "white"
                    game_players[game_id]["white"] = websocket
                elif Color.BLACK not in [player_colors.get(ws) for ws in connections[game_id]]:
                    player_colors[websocket] = "black"
                    player_color = "black"
                    game_players[game_id]["black"] = websocket
                else:
                    player_colors[websocket] = "spectator"
                    player_color = "spectator"
                
                await websocket.send_text(ChessProtocol.create_message(
                    "player_assignment", 
                    {"color": player_color}
                ))
                
                # Send initial board state
                await websocket.send_text(ChessProtocol.create_message(
                    MESSAGE_TYPES["BOARD_STATE"], 
                    {"board": ChessProtocol.board_to_dict(_active_games[game_id])}
                ))
                
                # Notify other players
                await broadcast(game_id, ChessProtocol.create_message(
                    "player_joined", 
                    {"color": player_color, "total_players": len(connections[game_id])}
                ), websocket)
                
                # Update game status
                if len(connections[game_id]) >= 2:
                    available_games[game_id]["status"] = "playing"
                    await broadcast(game_id, ChessProtocol.create_message(
                        "game_started", 
                        {"message": "Game is ready to play!"}
                    ))
                
                await broadcast_game_list()
                
            elif msg_type == MESSAGE_TYPES["MOVE"]:
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(
                        MESSAGE_TYPES["ERROR"], 
                        {"message": "Not joined to a game"}
                    ))
                    continue
                    
                # Check if it's player's turn
                board = _active_games[game_id]
                current_color = "white" if board.turn == Color.WHITE else "black"
                if player_colors.get(websocket) != current_color:
                    await websocket.send_text(ChessProtocol.create_message(
                        MESSAGE_TYPES["ERROR"], 
                        {"message": "Not your turn"}
                    ))
                    continue
                    
                move_data = message.get("move")
                try:
                    move = ChessProtocol.dict_to_move(move_data)
                    legal_moves = list(board.legal_moves(board.turn))
                    if move not in legal_moves:
                        await websocket.send_text(ChessProtocol.create_message(
                            MESSAGE_TYPES["ERROR"], 
                            {"message": "Illegal move"}
                        ))
                        continue
                        
                    board._make_move(move)
                    result = board.result()
                    
                    if result:
                        msg = ChessProtocol.create_message(
                            MESSAGE_TYPES["GAME_RESULT"], 
                            {"result": result, "board": ChessProtocol.board_to_dict(board)}
                        )
                        await broadcast(game_id, msg)
                    else:
                        msg = ChessProtocol.create_message(
                            MESSAGE_TYPES["BOARD_STATE"], 
                            {"board": ChessProtocol.board_to_dict(board)}
                        )
                        await broadcast(game_id, msg)
                        
                except Exception as e:
                    await websocket.send_text(ChessProtocol.create_message(
                        MESSAGE_TYPES["ERROR"], 
                        {"message": f"Error processing move: {str(e)}"}
                    ))
                    
            elif msg_type == MESSAGE_TYPES["BOARD_STATE"]:
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(
                        MESSAGE_TYPES["ERROR"], 
                        {"message": "Not joined to a game"}
                    ))
                    continue
                board = _active_games[game_id]
                await websocket.send_text(ChessProtocol.create_message(
                    MESSAGE_TYPES["BOARD_STATE"], 
                    {"board": ChessProtocol.board_to_dict(board)}
                ))
                
            elif msg_type == MESSAGE_TYPES["LEGAL_MOVES"]:
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(
                        MESSAGE_TYPES["ERROR"], 
                        {"message": "Not joined to a game"}
                    ))
                    continue
                board = _active_games[game_id]
                moves = list(board.legal_moves(board.turn))
                moves_dict = [ChessProtocol.move_to_dict(m) for m in moves]
                await websocket.send_text(ChessProtocol.create_message(
                    MESSAGE_TYPES["LEGAL_MOVES"], 
                    {"moves": moves_dict}
                ))
                
            elif msg_type == MESSAGE_TYPES["EVALUATION"]:
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(
                        MESSAGE_TYPES["ERROR"], 
                        {"message": "Not joined to a game"}
                    ))
                    continue
                board = _active_games[game_id]
                from chess_engine import evaluate_board
                eval_score = evaluate_board(board, Color.WHITE)
                await websocket.send_text(ChessProtocol.create_message(
                    MESSAGE_TYPES["EVALUATION"], 
                    {"evaluation": eval_score / 100.0}
                ))
                
            elif msg_type == MESSAGE_TYPES["AI_MOVE"]:
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(
                        MESSAGE_TYPES["ERROR"], 
                        {"message": "Not joined to a game"}
                    ))
                    continue
                board = _active_games[game_id]
                from chess_engine import find_best_move_parallel
                depth = message.get("depth", 4)
                try:
                    ai_move = find_best_move_parallel(board, board.turn, depth)
                    if ai_move:
                        board._make_move(ai_move)
                        result = board.result()
                        if result:
                            msg = ChessProtocol.create_message(
                                MESSAGE_TYPES["GAME_RESULT"], 
                                {"result": result, "board": ChessProtocol.board_to_dict(board)}
                            )
                            await broadcast(game_id, msg)
                        else:
                            msg = ChessProtocol.create_message(
                                MESSAGE_TYPES["AI_MOVE"], 
                                {"move": ChessProtocol.move_to_dict(ai_move), "board": ChessProtocol.board_to_dict(board)}
                            )
                            await broadcast(game_id, msg)
                    else:
                        await websocket.send_text(ChessProtocol.create_message(
                            MESSAGE_TYPES["ERROR"], 
                            {"message": "No legal moves available"}
                        ))
                except Exception as e:
                    await websocket.send_text(ChessProtocol.create_message(
                        MESSAGE_TYPES["ERROR"], 
                        {"message": f"Error calculating AI move: {str(e)}"}
                    ))
            else:
                await websocket.send_text(ChessProtocol.create_message(
                    MESSAGE_TYPES["ERROR"], 
                    {"message": f"Unknown message type: {msg_type}"}
                ))
                
    except WebSocketDisconnect:
        if game_id and websocket in connections.get(game_id, set()):
            connections[game_id].remove(websocket)
            player_colors.pop(websocket, None)
            
            # Remove from game_players if applicable
            if game_id in game_players:
                for color, ws in list(game_players[game_id].items()):
                    if ws == websocket:
                        del game_players[game_id][color]
            
            # Notify other players
            if game_id in connections and connections[game_id]:
                await broadcast(game_id, ChessProtocol.create_message(
                    "player_disconnected", 
                    {"message": "A player has disconnected"}
                ))
            
            # Clean up empty games
            if game_id in connections and not connections[game_id]:
                del connections[game_id]
                del _active_games[game_id]
                if game_id in game_players:
                    del game_players[game_id]
                if game_id in available_games:
                    del available_games[game_id]
            
            await broadcast_game_list()
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run("websocket_server:app", host=SOCKET_HOST, port=SOCKET_PORT, reload=False) 