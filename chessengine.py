import sys
from enum import Enum
from dataclasses import dataclass
from copy import deepcopy

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QMessageBox,
    QDialog, QDialogButtonBox, QVBoxLayout, QPushButton
)
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer

class Color(Enum):
    WHITE = 0
    BLACK = 1

    def opposite(self):
        return Color.WHITE if self == Color.BLACK else Color.BLACK

class PieceType(Enum):
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5

UNICODE_PIECES = {
    (Color.WHITE, PieceType.KING): "♔",
    (Color.WHITE, PieceType.QUEEN): "♕",
    (Color.WHITE, PieceType.ROOK): "♖",
    (Color.WHITE, PieceType.BISHOP): "♗",
    (Color.WHITE, PieceType.KNIGHT): "♘",
    (Color.WHITE, PieceType.PAWN): "♙",
    (Color.BLACK, PieceType.KING): "♚",
    (Color.BLACK, PieceType.QUEEN): "♛",
    (Color.BLACK, PieceType.ROOK): "♜",
    (Color.BLACK, PieceType.BISHOP): "♝",
    (Color.BLACK, PieceType.KNIGHT): "♞",
    (Color.BLACK, PieceType.PAWN): "♟",
}

@dataclass
class Piece:
    color: Color
    kind: PieceType
    has_moved: bool = False

@dataclass
class Move:
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    promotion: PieceType | None = None
    is_en_passant: bool = False
    is_castling: bool = False

    def __str__(self) -> str:  # Human readable
        cols = "abcdefgh"
        return f"{cols[self.from_col]}{8 - self.from_row}→{cols[self.to_col]}{8 - self.to_row}"


