import json
from typing import Dict, Any, Optional
from chess_engine import Board, Move, Color, PieceType, Piece
from chess_engine import _hash0

class ChessProtocol:
    """Handles chess protocol messages over TCP socket."""
    
    @staticmethod
    def create_message(msg_type: str, data: Dict[str, Any] = None) -> str:
        """Create a JSON message."""
        message = {"type": msg_type}
        if data:
            message.update(data)
        return json.dumps(message) + "\n"
    
    @staticmethod
    def parse_message(data: str) -> Optional[Dict[str, Any]]:
        """Parse a JSON message."""
        try:
            return json.loads(data.strip())
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def move_to_dict(move: Move) -> Dict[str, Any]:
        """Convert a Move object to a dictionary."""
        return {
            "from_row": move.from_row,
            "from_col": move.from_col,
            "to_row": move.to_row,
            "to_col": move.to_col,
            "promotion": move.promotion.value if move.promotion else None,
            "is_en_passant": move.is_en_passant,
            "is_castling": move.is_castling
        }
    
    @staticmethod
    def dict_to_move(data: Dict[str, Any]) -> Move:
        """Convert a dictionary to a Move object."""
        promotion = None
        if data.get("promotion"):
            promotion = PieceType(data["promotion"])
        
        return Move(
            from_row=data["from_row"],
            from_col=data["from_col"],
            to_row=data["to_row"],
            to_col=data["to_col"],
            promotion=promotion,
            is_en_passant=data.get("is_en_passant", False),
            is_castling=data.get("is_castling", False)
        )
    
    @staticmethod
    def board_to_dict(board: Board) -> Dict[str, Any]:
        """Convert a Board object to a dictionary."""
        grid = []
        for piece in board.grid:
            if piece is None:
                grid.append(None)
            else:
                grid.append({
                    "color": piece.color.value,
                    "kind": piece.kind.value,
                    "has_moved": piece.has_moved
                })
        # Convert castling_rights keys to strings
        castling_rights = {
            str(color.name).lower(): rights
            for color, rights in board.castling_rights.items()
        }
        return {
            "grid": grid,
            "turn": board.turn.value,
            "en_passant_target": board.en_passant_target,
            "castling_rights": castling_rights,
            "halfmove_clock": board.halfmove_clock,
            "fullmove_number": board.fullmove_number
        }
    
    @staticmethod
    def dict_to_board(data: Dict[str, Any]) -> Board:
        """Convert a dictionary to a Board object."""
        board = Board()
        board.grid = []
        for piece_data in data["grid"]:
            if piece_data is None:
                board.grid.append(None)
            else:
                board.grid.append(
                    Piece(
                        color=Color(piece_data["color"]),
                        kind=PieceType(piece_data["kind"]),
                        has_moved=piece_data["has_moved"]
                    )
                )
        board.turn = Color(data["turn"])
        board.en_passant_target = data["en_passant_target"]
        # Convert castling_rights keys back to Color enums
        castling_rights = {}
        for color_str, rights in data["castling_rights"].items():
            if color_str == "white":
                castling_rights[Color.WHITE] = rights
            elif color_str == "black":
                castling_rights[Color.BLACK] = rights
        board.castling_rights = castling_rights
        board.halfmove_clock = data["halfmove_clock"]
        board.fullmove_number = data["fullmove_number"]
        board._hash = _hash0(board.grid, board.turn, board.castling_rights, board.en_passant_target)
        return board

# Message types
MESSAGE_TYPES = {
    "MOVE": "move",
    "BOARD_STATE": "board_state", 
    "GAME_RESULT": "game_result",
    "LEGAL_MOVES": "legal_moves",
    "EVALUATION": "evaluation",
    "AI_MOVE": "ai_move",
    "ERROR": "error"
} 