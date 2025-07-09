#!/usr/bin/env python3
import sys
from enum import Enum
from dataclasses import dataclass
from copy import deepcopy
import concurrent.futures

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QMessageBox,
    QDialog, QDialogButtonBox, QVBoxLayout, QPushButton, QComboBox
)
from PyQt6.QtGui import QPainter, QColor, QFont
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
        """Deep copy so we can test moves without mutating original state."""
        return deepcopy(self)

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

class BoardWidget(QWidget):
    """Interactive chessboard widget."""

    def __init__(self, board: Board, parent=None):
        super().__init__(parent)
        self.board = board
        self.square = 64  # px
        self.setMinimumSize(QSize(self.square * 8, self.square * 8))
        self.setFont(QFont("Arial", 32))
        self.selected: tuple[int, int] | None = None
        self.candidates: list[Move] = []

    def paintEvent(self, _):
        p = QPainter(self)
        light, dark = QColor(240, 217, 181), QColor(181, 136, 99)
        hi_sel = QColor(246, 246, 105, 100)
        hi_move = QColor(246, 246, 105, 160)

        for r in range(8):
            for c in range(8):
                rect = (c * self.square, r * self.square, self.square, self.square)
                p.fillRect(*rect, light if (r + c) % 2 == 0 else dark)

                if self.selected == (r, c):
                    p.fillRect(*rect, hi_sel)
                elif any(mv.to_row == r and mv.to_col == c for mv in self.candidates):
                    p.fillRect(*rect, hi_move)

                piece = self.board._piece_at(r, c)
                if piece:
                    p.drawText(QPoint(c * self.square + self.square // 4,
                                      r * self.square + int(self.square * 0.75)),
                                UNICODE_PIECES[(piece.color, piece.kind)])

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


class ModeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Game Mode")
        layout = QVBoxLayout(self)
        self.mode = None
        btn2p = QPushButton("Two Player")
        btnai = QPushButton("Play vs AI")
        layout.addWidget(btn2p)
        layout.addWidget(btnai)
        btn2p.clicked.connect(lambda: self._choose("2p"))
        btnai.clicked.connect(lambda: self._choose("ai"))
    def _choose(self, mode):
        self.mode = mode
        self.accept()

class ColorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Your Color")
        layout = QVBoxLayout(self)
        self.color = None
        btnw = QPushButton("White")
        btnb = QPushButton("Black")
        layout.addWidget(btnw)
        layout.addWidget(btnb)
        btnw.clicked.connect(lambda: self._choose(Color.WHITE))
        btnb.clicked.connect(lambda: self._choose(Color.BLACK))
    def _choose(self, color):
        self.color = color
        self.accept()

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
        dlg = ModeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.mode = dlg.mode
        if self.mode == "ai":
            cdlg = ColorDialog(self)
            if cdlg.exec() == QDialog.DialogCode.Accepted:
                self.ai_color = cdlg.color
                self.board.turn = Color.WHITE if self.ai_color == Color.BLACK else Color.WHITE
            else:
                self.ai_color = Color.BLACK  # fallback
        else:
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
        self._trans_table.clear()  # Clear transposition table for each new root search
        # Use minimax with alpha-beta pruning
        depth = 3 # You can increase for more strength
        best_score = float('-inf')
        best_move = None
        board = self.board
        moves = list(board.legal_moves(color))
        # Move ordering: captures first
        def move_score(mv):
            target = board._piece_at(mv.to_row, mv.to_col)
            return (target is not None, PIECE_VALUES[target.kind] if target else 0)
        moves.sort(key=move_score, reverse=True)
        for move in moves:
            clone = board.copy()
            clone._make_move(move)
            score = self._minimax(clone, depth - 1, float('-inf'), float('inf'), False, color)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _board_hash(self, board):
        # Hash based on piece positions, turn, castling rights, en passant
        pieces = tuple(
            (r, c, p.color.value, p.kind.value)
            for r in range(8) for c in range(8)
            if (p := board._piece_at(r, c))
        )
        turn = board.turn.value
        cr = tuple(
            (color.value, tuple(sorted(board.castling_rights[color].items())))
            for color in (Color.WHITE, Color.BLACK)
        )
        ep = board.en_passant_target
        return hash((pieces, turn, cr, ep))

    def _minimax(self, board, depth, alpha, beta, maximizing, ai_color):
        h = self._board_hash(board)
        if h in self._trans_table:
            cached_depth, cached_score = self._trans_table[h]
            if cached_depth >= depth:
                return cached_score
        if depth == 0 or board.result() is not None:
            return evaluate_board(board, ai_color)
        color = ai_color if maximizing else ai_color.opposite()
        moves = list(board.legal_moves(color))
        # Move ordering: captures first
        def move_score(mv):
            target = board._piece_at(mv.to_row, mv.to_col)
            return (target is not None, PIECE_VALUES[target.kind] if target else 0)
        moves.sort(key=move_score, reverse=True)
        if not moves:
            return evaluate_board(board, ai_color)
        if maximizing:
            value = float('-inf')
            for move in moves:
                clone = board.copy()
                clone._make_move(move)
                value = max(value, self._minimax(clone, depth - 1, alpha, beta, False, ai_color))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            self._trans_table[h] = (depth, value)
            return value
        else:
            value = float('inf')
            for move in moves:
                clone = board.copy()
                clone._make_move(move)
                value = min(value, self._minimax(clone, depth - 1, alpha, beta, True, ai_color))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            self._trans_table[h] = (depth, value)
            return value

def main():
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
