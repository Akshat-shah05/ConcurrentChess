import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from chess_engine import Board, Color
from chess_protocol import ChessProtocol, MESSAGE_TYPES

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SOCKET_HOST = '0.0.0.0'
SOCKET_PORT = 8766

_active_games = {}  # game_id -> Board
connections = {}    # game_id -> set of WebSocket
player_colors = {}  # WebSocket -> color

async def broadcast(game_id, message):
    for ws in connections.get(game_id, set()):
        try:
            await ws.send_text(message)
        except Exception:
            pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    game_id = None
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
            if msg_type == "join":
                game_id = message.get("game_id")
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": "Missing game_id in join"}))
                    continue
                if game_id not in _active_games:
                    _active_games[game_id] = Board()
                if game_id not in connections:
                    connections[game_id] = set()
                connections[game_id].add(websocket)
                # Assign color
                assigned = None
                colors_in_game = [player_colors.get(ws) for ws in connections[game_id]]
                if Color.WHITE not in colors_in_game:
                    player_colors[websocket] = Color.WHITE
                    assigned = "white"
                elif Color.BLACK not in colors_in_game:
                    player_colors[websocket] = Color.BLACK
                    assigned = "black"
                else:
                    assigned = "spectator"
                await websocket.send_text(ChessProtocol.create_message("player_assignment", {"color": assigned}))
                # Send initial board state
                await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["BOARD_STATE"], {"board": ChessProtocol.board_to_dict(_active_games[game_id])}))
            elif msg_type == MESSAGE_TYPES["MOVE"]:
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": "Not joined to a game"}))
                    continue
                move_data = message.get("move")
                board = _active_games[game_id]
                try:
                    move = ChessProtocol.dict_to_move(move_data)
                    legal_moves = list(board.legal_moves(board.turn))
                    if move not in legal_moves:
                        await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": "Illegal move"}))
                        continue
                    board._make_move(move)
                    result = board.result()
                    if result:
                        msg = ChessProtocol.create_message(MESSAGE_TYPES["GAME_RESULT"], {"result": result, "board": ChessProtocol.board_to_dict(board)})
                        await broadcast(game_id, msg)
                    else:
                        msg = ChessProtocol.create_message(MESSAGE_TYPES["BOARD_STATE"], {"board": ChessProtocol.board_to_dict(board)})
                        await broadcast(game_id, msg)
                except Exception as e:
                    await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": f"Error processing move: {str(e)}"}))
            elif msg_type == MESSAGE_TYPES["BOARD_STATE"]:
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": "Not joined to a game"}))
                    continue
                board = _active_games[game_id]
                await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["BOARD_STATE"], {"board": ChessProtocol.board_to_dict(board)}))
            elif msg_type == MESSAGE_TYPES["LEGAL_MOVES"]:
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": "Not joined to a game"}))
                    continue
                board = _active_games[game_id]
                moves = list(board.legal_moves(board.turn))
                moves_dict = [ChessProtocol.move_to_dict(m) for m in moves]
                await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["LEGAL_MOVES"], {"moves": moves_dict}))
            elif msg_type == MESSAGE_TYPES["EVALUATION"]:
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": "Not joined to a game"}))
                    continue
                board = _active_games[game_id]
                from chess_engine import evaluate_board
                eval_score = evaluate_board(board, Color.WHITE)
                await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["EVALUATION"], {"evaluation": eval_score / 100.0}))
            elif msg_type == MESSAGE_TYPES["AI_MOVE"]:
                if not game_id:
                    await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": "Not joined to a game"}))
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
                            msg = ChessProtocol.create_message(MESSAGE_TYPES["GAME_RESULT"], {"result": result, "board": ChessProtocol.board_to_dict(board)})
                            await broadcast(game_id, msg)
                        else:
                            msg = ChessProtocol.create_message(MESSAGE_TYPES["AI_MOVE"], {"move": ChessProtocol.move_to_dict(ai_move), "board": ChessProtocol.board_to_dict(board)})
                            await broadcast(game_id, msg)
                    else:
                        await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": "No legal moves available"}))
                except Exception as e:
                    await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": f"Error calculating AI move: {str(e)}"}))
            else:
                await websocket.send_text(ChessProtocol.create_message(MESSAGE_TYPES["ERROR"], {"message": f"Unknown message type: {msg_type}"}))
    except WebSocketDisconnect:
        if game_id and websocket in connections.get(game_id, set()):
            connections[game_id].remove(websocket)
            player_colors.pop(websocket, None)
            # Optionally notify others
            # await broadcast(game_id, ChessProtocol.create_message("opponent_disconnected", {}))
    except Exception as e:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run("websocket_server:app", host=SOCKET_HOST, port=SOCKET_PORT, reload=False) 