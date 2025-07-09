#!/usr/bin/env python3
import sys
from enum import Enum
from dataclasses import dataclass
from copy import deepcopy
import concurrent.futures

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QMessageBox,
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QRadioButton, QGroupBox, QButtonGroup, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QPainter, QColor, QFont, QPixmap
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer

class Color(Enum):
    WHITE = 0
    BLACK = 1

    def opposite(self):
        return Color.BLACK if self is Color.WHITE else Color.WHITE


class PieceType(Enum):
    PAWN = "P"
    KNIGHT = "N"
    BISHOP = "B"
    ROOK = "R"
    QUEEN = "Q"
    KING = "K"


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
    """Represents a single move on the board."""
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


# Piece values
PIECE_VALUES = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
    PieceType.KING: 0,  # King value is not used directly
}

# Piece-square tables (from White's perspective, 8x8)
# Values from https://www.chessprogramming.org/Simplified_Evaluation_Function
PAWN_TABLE = [
      0,   0,   0,   0,   0,   0,   0,   0,
     50,  50,  50,  50,  50,  50,  50,  50,
     10,  10,  20,  30,  30,  20,  10,  10,
      5,   5,  10,  25,  25,  10,   5,   5,
      0,   0,   0,  20,  20,   0,   0,   0,
      5,  -5, -10,   0,   0, -10,  -5,   5,
      5,  10,  10, -20, -20,  10,  10,   5,
      0,   0,   0,   0,   0,   0,   0,   0
]
KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]
BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
]
ROOK_TABLE = [
      0,   0,   0,   0,   0,   0,   0,   0,
      5,  10,  10,  10,  10,  10,  10,   5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
      0,   0,   0,   5,   5,   0,   0,   0
]
QUEEN_TABLE = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20
]
KING_TABLE_MID = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20
]
KING_TABLE_END = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -30,   0,   0,   0,   0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]

PIECE_SQUARE_TABLES = {
    PieceType.PAWN: PAWN_TABLE,
    PieceType.KNIGHT: KNIGHT_TABLE,
    PieceType.BISHOP: BISHOP_TABLE,
    PieceType.ROOK: ROOK_TABLE,
    PieceType.QUEEN: QUEEN_TABLE,
    PieceType.KING: KING_TABLE_MID,  # For simplicity, use midgame table always
}

def evaluate_board(board: 'Board', color: Color) -> int:
    """
    Evaluate the board from the perspective of 'color'.
    Positive = good for 'color', negative = good for opponent.
    """
    score = 0
    for r in range(8):
        for c in range(8):
            p = board._piece_at(r, c)
            if not p:
                continue
            value = PIECE_VALUES[p.kind]
            # Piece-square table: flip for black
            pst = PIECE_SQUARE_TABLES[p.kind]
            idx = r * 8 + c if p.color == Color.WHITE else (7 - r) * 8 + c
            value += pst[idx]
            if p.color == color:
                score += value
            else:
                score -= value
    # Mobility
    my_moves = len(list(board.legal_moves(color)))
    opp_moves = len(list(board.legal_moves(color.opposite())))
    score += 5 * (my_moves - opp_moves)
    return score

class Board:
    """Holds the full game state and implements move‑generation/validation."""

    def __init__(self):
        self.grid: list[list[Piece | None]] = [[None] * 8 for _ in range(8)]
        self.turn: Color = Color.WHITE
        self.en_passant_target: tuple[int, int] | None = None  # Square that can be captured en‑passant.
        self.castling_rights = {Color.WHITE: {"K": True, "Q": True},
                                Color.BLACK: {"K": True, "Q": True}}
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self._setup_initial_position()

    @staticmethod
    def _in_bounds(r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def _piece_at(self, r: int, c: int):
        return self.grid[r][c] if self._in_bounds(r, c) else None

    def copy(self):
        clone = Board.__new__(Board)          # bypass __init__
        clone.turn               = self.turn
        clone.en_passant_target  = self.en_passant_target
        clone.castling_rights    = {
            Color.WHITE: self.castling_rights[Color.WHITE].copy(),
            Color.BLACK: self.castling_rights[Color.BLACK].copy()
        }
        clone.halfmove_clock     = self.halfmove_clock
        clone.fullmove_number    = self.fullmove_number
        # copy grid & Piece objects
        clone.grid = [
            [None if p is None else Piece(p.color, p.kind, p.has_moved)
             for p in row]
            for row in self.grid
        ]
        return clone

    def _setup_initial_position(self):
        # Pawns
        for c in range(8):
            self.grid[6][c] = Piece(Color.WHITE, PieceType.PAWN)
            self.grid[1][c] = Piece(Color.BLACK, PieceType.PAWN)
        # Other pieces
        order = [PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP, PieceType.QUEEN,
                 PieceType.KING, PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK]
        for c, kind in enumerate(order):
            self.grid[7][c] = Piece(Color.WHITE, kind)
            self.grid[0][c] = Piece(Color.BLACK, kind)

    # ─────────────────────────────  Move generation  ───────────────────────────── #

    def legal_moves(self, color: Color):
        """Generate all *legal* moves (i.e. not leaving own king in check)."""
        for move in self._pseudo_moves(color):
            clone = self.copy()
            clone._make_move(move)
            if not clone._in_check(color):
                yield move

    # Pseudo‑legal = obeys piece movement but ignores check.
    def _pseudo_moves(self, color: Color, include_castling: bool = True):
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.color is color:
                    yield from self._piece_moves(r, c, p, include_castling=include_castling)

    # Dispatch per piece‑type
    def _piece_moves(self, r: int, c: int, piece: Piece, include_castling: bool = True):
        match piece.kind:
            case PieceType.PAWN:
                yield from self._pawn_moves(r, c, piece)
            case PieceType.KNIGHT:
                yield from self._knight_moves(r, c, piece)
            case PieceType.BISHOP:
                yield from self._bishop_moves(r, c, piece)
            case PieceType.ROOK:
                yield from self._rook_moves(r, c, piece)
            case PieceType.QUEEN:
                yield from self._queen_moves(r, c, piece)
            case PieceType.KING:
                yield from self._king_moves(r, c, piece, include_castling=include_castling)

    def _pawn_moves(self, r: int, c: int, piece: Piece):
        dir_ = -1 if piece.color is Color.WHITE else 1
        start_row = 6 if piece.color is Color.WHITE else 1

        # one‑square forward
        if self._piece_at(r + dir_, c) is None:
            if r + dir_ in (0, 7):  # promotion
                for promo in (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT):
                    yield Move(r, c, r + dir_, c, promotion=promo)
            else:
                yield Move(r, c, r + dir_, c)
            # double‑step
            if r == start_row and self._piece_at(r + 2 * dir_, c) is None:
                yield Move(r, c, r + 2 * dir_, c)

        # captures (diagonals)
        for dc in (-1, 1):
            tr, tc = r + dir_, c + dc
            if not self._in_bounds(tr, tc):
                continue
            target = self._piece_at(tr, tc)
            if target and target.color is not piece.color:
                if tr in (0, 7):
                    for promo in (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT):
                        yield Move(r, c, tr, tc, promotion=promo)
                else:
                    yield Move(r, c, tr, tc)
            # en‑passant
            if self.en_passant_target == (tr, tc):
                yield Move(r, c, tr, tc, is_en_passant=True)

    def _knight_moves(self, r, c, piece):
        for dr, dc in ((2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)):
            tr, tc = r + dr, c + dc
            if not self._in_bounds(tr, tc):
                continue
            target = self._piece_at(tr, tc)
            if target is None or target.color is not piece.color:
                yield Move(r, c, tr, tc)

    def _sliding(self, r, c, piece, directions):
        for dr, dc in directions:
            tr, tc = r + dr, c + dc
            while self._in_bounds(tr, tc):
                target = self._piece_at(tr, tc)
                if target is None:
                    yield Move(r, c, tr, tc)
                else:
                    if target.color is not piece.color:
                        yield Move(r, c, tr, tc)
                    break
                tr += dr
                tc += dc

    def _bishop_moves(self, r, c, piece):
        yield from self._sliding(r, c, piece, ((1, 1), (1, -1), (-1, 1), (-1, -1)))

    def _rook_moves(self, r, c, piece):
        yield from self._sliding(r, c, piece, ((1, 0), (-1, 0), (0, 1), (0, -1)))

    def _queen_moves(self, r, c, piece):
        yield from self._sliding(r, c, piece, ((1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)))

    def _king_moves(self, r, c, piece, include_castling: bool = True):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                tr, tc = r + dr, c + dc
                if not self._in_bounds(tr, tc):
                    continue
                target = self._piece_at(tr, tc)
                if target is None or target.color is not piece.color:
                    yield Move(r, c, tr, tc)
        # Castling
        if include_castling:
            rights = self.castling_rights[piece.color]
            back_rank = 7 if piece.color is Color.WHITE else 0
            if (r, c) == (back_rank, 4) and not piece.has_moved and not self._in_check(piece.color):
                # King‑side  (columns 5,6 must be empty)
                if rights["K"] and all(self._piece_at(back_rank, col) is None for col in (5, 6)):
                    if not self._square_attacked(back_rank, 5, piece.color.opposite()) and not self._square_attacked(back_rank, 6, piece.color.opposite()):
                        yield Move(r, c, back_rank, 6, is_castling=True)
                # Queen‑side (columns 1,2,3 empty)
                if rights["Q"] and all(self._piece_at(back_rank, col) is None for col in (1, 2, 3)):
                    if not self._square_attacked(back_rank, 3, piece.color.opposite()) and not self._square_attacked(back_rank, 2, piece.color.opposite()):
                        yield Move(r, c, back_rank, 2, is_castling=True)

    def _make_move(self, mv: Move):
        piece = self.grid[mv.from_row][mv.from_col]
        target = self._piece_at(mv.to_row, mv.to_col)

        # Reset half‑move clock if pawn move or capture
        if piece.kind is PieceType.PAWN or target is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Castling rook move
        if mv.is_castling:
            if mv.to_col == 6:  # King‑side
                rook_from, rook_to = (mv.from_row, 7), (mv.from_row, 5)
            else:  # Queen‑side
                rook_from, rook_to = (mv.from_row, 0), (mv.from_row, 3)
            rook = self._piece_at(*rook_from)
            self.grid[rook_from[0]][rook_from[1]] = None
            self.grid[rook_to[0]][rook_to[1]] = rook
            rook.has_moved = True

        # En‑passant capture (remove the pawn that was bypassed last move)
        if mv.is_en_passant:
            self.grid[mv.from_row][mv.to_col] = None

        # Move the actual piece
        self.grid[mv.from_row][mv.from_col] = None
        self.grid[mv.to_row][mv.to_col] = piece
        piece.has_moved = True

        # Promotion
        if piece.kind is PieceType.PAWN and mv.promotion:
            self.grid[mv.to_row][mv.to_col] = Piece(piece.color, mv.promotion, has_moved=True)

        # Update en‑passant target square
        if piece.kind is PieceType.PAWN and abs(mv.to_row - mv.from_row) == 2:
            self.en_passant_target = ((mv.from_row + mv.to_row) // 2, mv.from_col)
        else:
            self.en_passant_target = None

        # Update castling rights if king or rook moved/captured
        if piece.kind is PieceType.KING:
            self.castling_rights[piece.color]["K"] = False
            self.castling_rights[piece.color]["Q"] = False
        if piece.kind is PieceType.ROOK:
            if mv.from_col == 0:
                self.castling_rights[piece.color]["Q"] = False
            elif mv.from_col == 7:
                self.castling_rights[piece.color]["K"] = False
        if target and target.kind is PieceType.ROOK:
            if mv.to_col == 0:
                self.castling_rights[target.color]["Q"] = False
            elif mv.to_col == 7:
                self.castling_rights[target.color]["K"] = False

        # Increment move numbers / switch turn
        if self.turn is Color.BLACK:
            self.fullmove_number += 1
        self.turn = self.turn.opposite()

    # ────────────────────────────────  Checks  ──────────────────────────────── #

    def _square_attacked(self, r: int, c: int, by_color: Color):
        return any(mv.to_row == r and mv.to_col == c for mv in self._pseudo_moves(by_color, include_castling=False))

    def _king_pos(self, color: Color):
        for r in range(8):
            for c in range(8):
                p = self._piece_at(r, c)
                if p and p.color is color and p.kind is PieceType.KING:
                    return r, c
        return None

    def _in_check(self, color: Color):
        kp = self._king_pos(color)
        return kp and self._square_attacked(*kp, color.opposite())

    # ─────────────────────────────  End‑of‑game  ───────────────────────────── #

    def result(self):
        moves = list(self.legal_moves(self.turn))
        if not moves:
            if self._in_check(self.turn):
                return f"Checkmate! {'White' if self.turn is Color.BLACK else 'Black'} wins."
            return "Stalemate!"
        if self.halfmove_clock >= 100:
            return "Draw by 50‑move rule."
        return None

# Modern combined dialog for mode and color selection
class GameSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Start New Game")
        self.setMinimumWidth(320)
        layout = QVBoxLayout(self)

        # Mode selection
        mode_group = QGroupBox("Game Mode")
        mode_layout = QVBoxLayout()
        self.rb_2p = QRadioButton("Two Player")
        self.rb_ai = QRadioButton("Play vs AI")
        self.rb_2p.setChecked(True)
        mode_layout.addWidget(self.rb_2p)
        mode_layout.addWidget(self.rb_ai)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Color selection (only enabled if AI)
        color_group = QGroupBox("Your Color")
        color_layout = QHBoxLayout()
        self.rb_white = QRadioButton("White")
        self.rb_black = QRadioButton("Black")
        self.rb_white.setChecked(True)
        color_layout.addWidget(self.rb_white)
        color_layout.addWidget(self.rb_black)
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # Enable/disable color selection based on mode
        def update_color_enabled():
            color_group.setEnabled(self.rb_ai.isChecked())
        self.rb_2p.toggled.connect(update_color_enabled)
        self.rb_ai.toggled.connect(update_color_enabled)
        update_color_enabled()

        # OK/Cancel buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @property
    def mode(self):
        return "ai" if self.rb_ai.isChecked() else "2p"

    @property
    def color(self):
        return Color.WHITE if self.rb_white.isChecked() else Color.BLACK

# Place BoardWidget here, before MainWindow
class BoardWidget(QWidget):
    def __init__(self, board: Board, parent=None):
        super().__init__(parent)
        self.board = board
        self.square = 72  # px, larger for better visuals
        self.margin = 16  # px, padding around the board
        self.setMinimumSize(QSize(self.square * 8 + 2 * self.margin, self.square * 8 + 2 * self.margin))
        self.setFont(QFont("Arial Unicode MS", 40, QFont.Weight.Bold))
        self.selected: tuple[int, int] | None = None
        self.candidates: list[Move] = []
        # Load piece images
        self.piece_images = {}
        import os
        piece_codes = {
            (Color.WHITE, PieceType.KING): 'wK',
            (Color.WHITE, PieceType.QUEEN): 'wQ',
            (Color.WHITE, PieceType.ROOK): 'wR',
            (Color.WHITE, PieceType.BISHOP): 'wB',
            (Color.WHITE, PieceType.KNIGHT): 'wN',
            (Color.WHITE, PieceType.PAWN): 'wP',
            (Color.BLACK, PieceType.KING): 'bK',
            (Color.BLACK, PieceType.QUEEN): 'bQ',
            (Color.BLACK, PieceType.ROOK): 'bR',
            (Color.BLACK, PieceType.BISHOP): 'bB',
            (Color.BLACK, PieceType.KNIGHT): 'bN',
            (Color.BLACK, PieceType.PAWN): 'bP',
        }
        for key, code in piece_codes.items():
            path = os.path.join(os.path.dirname(__file__), 'pieces', f'{code}.png')
            if os.path.exists(path):
                self.piece_images[key] = QPixmap(path)
            else:
                self.piece_images[key] = None

    def paintEvent(self, _):
        p = QPainter(self)
        # High-contrast palette for white Unicode pieces
        light = QColor(120, 150, 180)  # muted blue
        dark = QColor(40, 60, 80)      # deep navy
        hi_sel = QColor(255, 215, 0, 120)      # gold highlight for selected
        hi_move = QColor(80, 200, 120, 120)    # green for possible moves
        hi_last = QColor(255, 255, 0, 60)      # yellow for last move

        # Draw board squares
        for r in range(8):
            for c in range(8):
                rect = (
                    self.margin + c * self.square,
                    self.margin + r * self.square,
                    self.square, self.square
                )
                p.fillRect(*rect, light if (r + c) % 2 == 0 else dark)

        # Highlight selected square
        if self.selected:
            r, c = self.selected
            rect = (
                self.margin + c * self.square,
                self.margin + r * self.square,
                self.square, self.square
            )
            p.fillRect(*rect, hi_sel)

        # Highlight candidate move targets
        for mv in self.candidates:
            rect = (
                self.margin + mv.to_col * self.square,
                self.margin + mv.to_row * self.square,
                self.square, self.square
            )
            p.fillRect(*rect, hi_move)

        # Draw pieces using PNGs, centered
        for r in range(8):
            for c in range(8):
                piece = self.board._piece_at(r, c)
                if piece:
                    img = self.piece_images.get((piece.color, piece.kind))
                    if img and not img.isNull():
                        rect_x = self.margin + c * self.square
                        rect_y = self.margin + r * self.square
                        p.drawPixmap(rect_x, rect_y, self.square, self.square, img)

    def mousePressEvent(self, evt):
        # Block input if AI is thinking
        mw = self.parentWidget()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parentWidget()
        if mw and getattr(mw, '_ai_thinking', False):
            return
        c = int(evt.position().x()) // self.square
        r = int(evt.position().y()) // self.square
        if not Board._in_bounds(r, c):
            return

        if self.selected:
            # Attempt to make a move
            for mv in self.candidates:
                if (mv.to_row, mv.to_col) == (r, c):
                    if mv.promotion and self.board.turn is Color.WHITE:
                        mv.promotion = self._choose_promotion()
                    elif mv.promotion and self.board.turn is Color.BLACK:
                        mv.promotion = PieceType.QUEEN  # auto‑queen for black to simplify UI
                    self.board._make_move(mv)
                    break
            self.selected, self.candidates = None, []
            self.update()
            if res := self.board.result():
                QMessageBox.information(self, "Game Over", res)
            return

        piece = self.board._piece_at(r, c)
        if piece and piece.color is self.board.turn:
            self.selected = (r, c)
            self.candidates = [m for m in self.board.legal_moves(piece.color) if (m.from_row, m.from_col) == (r, c)]
        else:
            self.selected, self.candidates = None, []
        self.update()

    def _choose_promotion(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Choose promotion piece")
        layout = QVBoxLayout(dlg)
        choice = {}
        for pt in (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT):
            btn = QPushButton(pt.name.title())
            layout.addWidget(btn)
            btn.clicked.connect(lambda _, x=pt: (choice.setdefault("p", x), dlg.accept()))
        dlg.exec()
        return choice.get("p", PieceType.QUEEN)

# MainWindow comes after BoardWidget
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Chess – PyQt6")
        self.board = Board()
        self.view = BoardWidget(self.board)
        self.setCentralWidget(self.view)
        self.status = QLabel()
        self.statusBar().addPermanentWidget(self.status)
        self.mode = "2p"  # default
        self.ai_color = None
        self._choose_mode_and_color()
        self._ai_thinking = False
        self._ai_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._ai_future = None
        self._trans_table = {}
        # Periodically refresh status bar and check for AI move
        timer = QTimer(self)
        timer.timeout.connect(self._refresh_status)
        timer.timeout.connect(self._maybe_do_ai_move)
        timer.start(200)

    def _choose_mode_and_color(self):
        dlg = GameSetupDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.mode = dlg.mode
            if self.mode == "ai":
                self.ai_color = dlg.color
                self.board.turn = Color.WHITE if self.ai_color == Color.BLACK else Color.WHITE
            else:
                self.ai_color = None
        else:
            self.mode = "2p"
            self.ai_color = None

    def _refresh_status(self):
        if res := self.board.result():
            self.status.setText(res)
        else:
            self.status.setText(f"{'White' if self.board.turn is Color.WHITE else 'Black'} to move")

    def _maybe_do_ai_move(self):
        if self.mode == "ai" and self.board.turn == self.ai_color and not self._ai_thinking and not self.board.result():
            self._ai_thinking = True
            # Start AI move in a background thread
            self._ai_future = self._ai_executor.submit(self._find_best_move, self.ai_color)
            QTimer.singleShot(100, self._check_ai_move_done)

    def _check_ai_move_done(self):
        if self._ai_future is None:
            return
        if self._ai_future.done():
            move = self._ai_future.result()
            if move:
                self.board._make_move(move)
                self.view.selected = None
                self.view.candidates = []
                self.view.update()
            self._ai_thinking = False
            self._ai_future = None
        else:
            QTimer.singleShot(100, self._check_ai_move_done)

    def _find_best_move(self, color):
        return find_best_move_parallel(self.board, color, depth=4)

    def _board_hash(board: 'Board'):
    pieces = tuple(
        (r, c, p.color.value, p.kind.value)
        for r in range(8) for c in range(8)
        if (p := board._piece_at(r, c))
    )
    return hash((pieces, board.turn.value,
                 tuple(sorted(board.castling_rights[Color.WHITE].items())),
                 tuple(sorted(board.castling_rights[Color.BLACK].items())),
                 board.en_passant_target))

def _minimax(board, depth, alpha, beta, maximizing, ai_color, tt):
    key = (_board_hash(board), depth, maximizing)
    if key in tt:
        return tt[key]

    if depth == 0 or board.result() is not None:
        return evaluate_board(board, ai_color)

    color = ai_color if maximizing else ai_color.opposite()
    moves = list(board.legal_moves(color))

    # Better ordering: (is_capture, value_of_capture)
    moves.sort(key=lambda mv: (
        (t := board._piece_at(mv.to_row, mv.to_col)) is not None,
        PIECE_VALUES.get(t.kind, 0) if t else 0
    ), reverse=True)

    if maximizing:
        best = float('-inf')
        for mv in moves:
            nb = board.copy()
            nb._make_move(mv)
            best = max(best, _minimax(nb, depth-1, alpha, beta, False, ai_color, tt))
            alpha = max(alpha, best)
            if alpha >= beta:
                break
    else:
        best = float('inf')
        for mv in moves:
            nb = board.copy()
            nb._make_move(mv)
            best = min(best, _minimax(nb, depth-1, alpha, beta, True, ai_color, tt))
            beta = min(beta, best)
            if beta <= alpha:
                break

    tt[key] = best
    return best


def _score_move(args):
    """Run inside a worker process – evaluate one root move."""
    board, move, ai_color, depth = args
    nb = board.copy()
    nb._make_move(move)
    score = _minimax(nb, depth-1, float('-inf'), float('inf'),
                     False, ai_color, {})      # local TT
    return score, move


def find_best_move_parallel(board: 'Board', ai_color: Color,
                            depth: int = 4) -> Move | None:
    moves = list(board.legal_moves(ai_color))
    if not moves:
        return None
    # Same ordering trick as above
    moves.sort(key=lambda mv: (
        (t := board._piece_at(mv.to_row, mv.to_col)) is not None,
        PIECE_VALUES.get(t.kind, 0) if t else 0
    ), reverse=True)

    # One big board object is pickled for each job – acceptable at root.
    with concurrent.futures.ProcessPoolExecutor(
            max_workers=os.cpu_count()) as pool:
        results = pool.map(_score_move,
                           ((board, mv, ai_color, depth) for mv in moves))
    best_score, best_move = max(results, key=lambda x: x[0])
    return best_move

def main():
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method("spawn", force=True)
    main()
