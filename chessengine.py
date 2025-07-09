#!/usr/bin/env python3
import os, sys, multiprocessing
from enum import Enum
from dataclasses import dataclass
from copy import deepcopy
import concurrent.futures
import functools, pickle

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


@dataclass (slots=True)
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

# ─────────────── Improved static evaluation (centipawns) ─────────────── #
def _game_phase(board: 'Board') -> float:
    """0.0 = early mid-game, 1.0 = deep end-game (no majors / few minors)."""
    phase = 0
    for p in board.grid:
        if not p or p.kind is PieceType.PAWN:
            continue
        phase += PIECE_VALUES[p.kind]
    # 40 cp ≈ both queens + one rook = typical transition
    return max(0.0, min(1.0, 1.0 - phase / 4000))

# helper masks for quick pawn-file tests
_FILE_MASKS = [ [(sq>>3, sq&7) for sq in range(f, 64, 8)] for f in range(8) ]

def _pawn_structure(board: 'Board', color: Color) -> int:
    """Isolated / doubled / passed pawns (centipawns, positive = good)."""
    pawns   = [ sq for sq,p in enumerate(board.grid) if p and p.color==color and p.kind is PieceType.PAWN ]
    oppside = Color.WHITE if color is Color.BLACK else Color.BLACK
    score   = 0
    files   = { sq & 7 for sq in pawns }

    for sq in pawns:
        file_ = sq & 7
        rank  = 7 - (sq>>3) if color is Color.WHITE else (sq>>3)
        # doubled
        if sum(1 for r,c in _FILE_MASKS[file_] if board.grid[(r<<3)|c]
               and board.grid[(r<<3)|c].color==color and
               board.grid[(r<<3)|c].kind is PieceType.PAWN ) > 1:
            score -= 15
        # isolated
        if {file_-1, file_+1}.isdisjoint(files):
            score -= 15
        # passed?
        passed = True
        for f in (file_-1, file_, file_+1):
            if not 0<=f<8: continue
            for r,c in _FILE_MASKS[f]:
                if (color is Color.WHITE and r < (sq>>3)) or (color is Color.BLACK and r > (sq>>3)):
                    pp = board.grid[(r<<3)|c]
                    if pp and pp.color==oppside and pp.kind is PieceType.PAWN:
                        passed=False; break
            if not passed: break
        if passed:
            score += 20 + rank*5
    return score

def _count_weighted_mobility(board:'Board', color:Color)->int:
    w = {PieceType.KNIGHT:4, PieceType.BISHOP:4,
         PieceType.ROOK:2,    PieceType.QUEEN:1}
    cnt = 0
    for mv in board._pseudo_moves(color, include_castling=False):
        piece = board.grid[board._sq(mv.from_row, mv.from_col)]
        cnt += w.get(piece.kind,0)
    return cnt

def _rook_file_bonus(board:'Board', color:Color)->int:
    bonus = 0
    opp = color.opposite()
    for sq,p in enumerate(board.grid):
        if not p or p.color!=color or p.kind is not PieceType.ROOK: continue
        file_ = sq & 7
        has_own_pawn = any( board.grid[(r<<3)|file_] and
                            board.grid[(r<<3)|file_].color==color and
                            board.grid[(r<<3)|file_].kind is PieceType.PAWN
                            for r in range(8))
        has_opp_pawn = any( board.grid[(r<<3)|file_] and
                            board.grid[(r<<3)|file_].color==opp and
                            board.grid[(r<<3)|file_].kind is PieceType.PAWN
                            for r in range(8))
        if not has_own_pawn and not has_opp_pawn:
            bonus += 15      # open
        elif not has_own_pawn and has_opp_pawn==False:
            bonus += 7       # semi-open
    return bonus

def _king_safety(board:'Board', color:Color, phase:float)->int:
    """Very cheap: pawn shield in front of castling position (only mid-game)."""
    if phase>0.7:   # in late end-game king safety ≈ 0
        return 0
    score = 0
    back = 7 if color is Color.WHITE else 0
    front = back-1 if color is Color.WHITE else back+1
    cols = (6,5,4) if color is Color.WHITE else (1,2,3)  # g,f,e or b,c,d
    for c in cols:
        if not any( board.grid[board._sq(r,c)]
                    and board.grid[board._sq(r,c)].color==color
                    and board.grid[board._sq(r,c)].kind is PieceType.PAWN
                    for r in (front,front-1) if 0<=front-1<8 ):
            score -= 12
    return score

def evaluate_board(board:'Board', color:Color)->int:
    """Return static evaluation in centipawns (positive = good for *color*)."""
    phase = _game_phase(board)      # blend factor 0..1

    mat   = 0
    pst   = 0
    counts= {Color.WHITE:{PieceType.BISHOP:0}, Color.BLACK:{PieceType.BISHOP:0}}
    for sq,p in enumerate(board.grid):
        if not p: continue
        sign = 1 if p.color is color else -1
        mat += sign * PIECE_VALUES[p.kind]
        table = PIECE_SQUARE_TABLES[p.kind]
        # king table blend
        if p.kind is PieceType.KING:
            mid = table[sq if p.color is Color.WHITE else ((7-(sq>>3))<<3 | (sq & 7))]
            end = KING_TABLE_END[sq if p.color is Color.WHITE else ((7-(sq>>3))<<3 | (sq & 7))]
            pst += sign * int( (1-phase)*mid + phase*end )
        else:
            idx = sq if p.color is Color.WHITE else ((7-(sq>>3))<<3 | (sq & 7))
            pst += sign * table[idx]
        if p.kind is PieceType.BISHOP:
            counts[p.color][PieceType.BISHOP]+=1

    bishop_pair = 50 * ( (counts[color][PieceType.BISHOP]==2) -
                         (counts[color.opposite()][PieceType.BISHOP]==2) )

    mobility = (_count_weighted_mobility(board,color) -
                _count_weighted_mobility(board,color.opposite())) * 3

    pawns = (_pawn_structure(board,color) -
             _pawn_structure(board,color.opposite()))

    rooks = (_rook_file_bonus(board,color) -
             _rook_file_bonus(board,color.opposite()))

    ksafety = (_king_safety(board,color,phase) -
               _king_safety(board,color.opposite(),phase))

    return mat + pst + bishop_pair + mobility + pawns + rooks + ksafety

# ──────────────────────  FAST-ENGINE EXTENSIONS  ────────────────────── #
import random, ctypes
RND64 = lambda: random.getrandbits(64)

# --- Zobrist tables --------------------------------------------------- #
_ZP  = {(clr, pt): [RND64() for _ in range(64)]
        for clr in (Color.WHITE, Color.BLACK)
        for pt  in PieceType}

_ZCASTLE = {  # KQkq
    (Color.WHITE, 'K'): RND64(), (Color.WHITE, 'Q'): RND64(),
    (Color.BLACK, 'K'): RND64(), (Color.BLACK, 'Q'): RND64()
}
_ZSIDE  = RND64()
_ZEP    = [RND64() for _ in range(8)]            # file of e.p. target

def _hash0(grid, turn, rights, ep):
    """Initial full hash (called **once** per game)."""
    h = 0
    for sq, p in enumerate(grid):
        if p:
            h ^= _ZP[(p.color, p.kind)][sq]
    for clr in (Color.WHITE, Color.BLACK):
        if rights[clr]['K']: h ^= _ZCASTLE[(clr, 'K')]
        if rights[clr]['Q']: h ^= _ZCASTLE[(clr, 'Q')]
    if ep: h ^= _ZEP[ep[1]]
    if turn is Color.BLACK: h ^= _ZSIDE
    return ctypes.c_uint64(h).value  # always fit in 64 bit

# --- Fast, no-allocation evaluate_board ---
@functools.lru_cache(maxsize=1_000_000)
def _eval_hash(h):           #  ≤ 30 ns after the first hit
    return h                 # placeholder – will never be called, only cached

# --- In-place alpha-beta search ---
def _search(board: 'Board', depth: int, alpha: int, beta: int,
            maximizing: bool, ai_color: Color, tt: dict[int, int]) -> int:
    """
    Fast negamax with transposition table – *board* is mutated in-place.
    """
    key = (board._hash, depth, maximizing)
    if (val := tt.get(key)) is not None:
        return val
    if depth == 0 or board.result():
        return evaluate_board(board, ai_color)

    best = -10_000_000 if maximizing else 10_000_000
    color = ai_color if maximizing else ai_color.opposite()
    moves = sorted(board.legal_moves(color),     # captures first
                   key=lambda m:(board._piece_at(m.to_row, m.to_col) is not None),
                   reverse=True)

    for mv in moves:
        token = board.push(mv)
        val   = _search(board, depth-1, alpha, beta, not maximizing,
                        ai_color, tt)
        board.pop(token)

        if maximizing:
            best  = max(best, val)
            alpha = max(alpha, best)
            if alpha >= beta: break
        else:
            best  = min(best, val)
            beta  = min(beta, best)
            if beta <= alpha: break
    tt[key] = best
    return best

# --- Parallel root split ---
def _score_single(board_bytes, mv_bytes, ai_color_value, depth):
    """
    Helper that runs in its *own* process – restores a lightweight Board,
    searches one branch, returns (score, move_bytes).
    """
    board = pickle.loads(board_bytes)
    mv    = pickle.loads(mv_bytes)
    token = board.push(mv)
    score = _search(board, depth-1, -10_000_000, 10_000_000,
                    maximizing=False, ai_color=Color(ai_color_value),
                    tt={})
    board.pop(token)
    return score, mv_bytes


def find_best_move_parallel(board: 'Board', ai_color: Color, depth: int = 4):
    moves = list(board.legal_moves(ai_color))
    if not moves: return None

    board_blob = pickle.dumps(board)   # done once

    with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
        futs = [ pool.submit(_score_single, board_blob, pickle.dumps(mv),
                             ai_color.value, depth) for mv in moves ]
        best = max(futs, key=lambda f: f.result()[0]).result()[1]

    return pickle.loads(best)

class Board:
    __slots__ = ("grid", "turn", "en_passant_target",
                 "castling_rights", "halfmove_clock",
                 "fullmove_number", "_hash")

    def __init__(self):
        self.grid: list[Piece | None] = [None] * 64
        self.turn  = Color.WHITE
        self.castling_rights = {Color.WHITE: {'K': True, 'Q': True},
                                Color.BLACK: {'K': True, 'Q': True}}
        self.en_passant_target = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self._setup_initial_position()
        self._hash = _hash0(self.grid, self.turn,
                            self.castling_rights, self.en_passant_target)

    # ───── helpers ───── #
    @staticmethod
    def _sq(r, c):             # map (row,col) → 0..63
        return (r << 3) | c

    @staticmethod
    def _rc(sq):               # inverse mapping
        return sq >> 3, sq & 7

    @staticmethod
    def _in_bounds(r, c):      # in-lined everywhere else in hot paths
        return 0 <= r < 8 and 0 <= c < 8

    def _piece_at(self, r, c):
        return self.grid[self._sq(r, c)]

    def copy(self):
        clone = Board.__new__(Board)
        clone.grid = [p if p is None else Piece(p.color, p.kind, getattr(p, 'has_moved', False))
                      for p in self.grid]
        clone.turn = self.turn
        clone.en_passant_target = self.en_passant_target
        clone.castling_rights = {
            Color.WHITE: self.castling_rights[Color.WHITE].copy(),
            Color.BLACK: self.castling_rights[Color.BLACK].copy()
        }
        clone.halfmove_clock = self.halfmove_clock
        clone.fullmove_number = self.fullmove_number
        clone._hash = self._hash
        return clone

    # ───── board initialisation ───── #
    def _setup_initial_position(self):
        order = [PieceType.ROOK, PieceType.KNIGHT, PieceType.BISHOP,
                 PieceType.QUEEN, PieceType.KING,
                 PieceType.BISHOP, PieceType.KNIGHT, PieceType.ROOK]
        # pawns
        for c in range(8):
            self.grid[self._sq(6, c)] = Piece(Color.WHITE, PieceType.PAWN)
            self.grid[self._sq(1, c)] = Piece(Color.BLACK, PieceType.PAWN)
        # back rank
        for c, pt in enumerate(order):
            self.grid[self._sq(7, c)] = Piece(Color.WHITE, pt)
            self.grid[self._sq(0, c)] = Piece(Color.BLACK, pt)

    # ───── move make / undo (no allocations) ───── #
    def push(self, mv: Move):
        """
        Execute *mv* and return an opaque token to restore the
        previous position – O(1), no copies.
        """
        f, t = self._sq(mv.from_row, mv.from_col), self._sq(mv.to_row, mv.to_col)
        piece           = self.grid[f]
        captured        = self.grid[t]
        ep_old          = self.en_passant_target
        rights_snapshot = (self.castling_rights[Color.WHITE]['K'],
                           self.castling_rights[Color.WHITE]['Q'],
                           self.castling_rights[Color.BLACK]['K'],
                           self.castling_rights[Color.BLACK]['Q'])
        halfmove_old    = self.halfmove_clock
        hash_old        = self._hash

        # HASH out moving piece from old square
        self._hash ^= _ZP[(piece.color, piece.kind)][f]
        # HASH out side to move
        self._hash ^= _ZSIDE

        # Reset 50-move clock if capture or pawn push
        if captured or piece.kind is PieceType.PAWN:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # --- handle special cases ---------------------------------------- #
        rook_from = rook_to = rook_piece = None
        if mv.is_castling:      # update rook as well
            if mv.to_col == 6:  # king side
                rook_from, rook_to = self._sq(mv.from_row, 7), self._sq(mv.from_row, 5)
            else:               # queen side
                rook_from, rook_to = self._sq(mv.from_row, 0), self._sq(mv.from_row, 3)
            rook_piece = self.grid[rook_from]
            self.grid[rook_to] = rook_piece
            self.grid[rook_from] = None
            self._hash ^= _ZP[(rook_piece.color, rook_piece.kind)][rook_from]
            self._hash ^= _ZP[(rook_piece.color, rook_piece.kind)][rook_to]

        if mv.is_en_passant:
            cap_sq = self._sq(mv.from_row, mv.to_col)
            captured = self.grid[cap_sq]
            self.grid[cap_sq] = None
            if captured:
                self._hash ^= _ZP[(captured.color, captured.kind)][cap_sq]

        # HASH out captured piece
        if captured:
            self._hash ^= _ZP[(captured.color, captured.kind)][t]

        # move piece
        self.grid[t] = piece
        self.grid[f] = None
        self._hash ^= _ZP[(piece.color, piece.kind)][t]

        # promotion
        promoted_kind = piece.kind
        if mv.promotion:
            promoted_kind = mv.promotion
            self._hash ^= _ZP[(piece.color, piece.kind)][t]
            self._hash ^= _ZP[(piece.color, promoted_kind)][t]
            self.grid[t] = Piece(piece.color, promoted_kind)

        # en-passant file hashing
        if self.en_passant_target:
            self._hash ^= _ZEP[self.en_passant_target[1]]
        self.en_passant_target = None
        if piece.kind is PieceType.PAWN and abs(mv.to_row - mv.from_row) == 2:
            self.en_passant_target = ((mv.from_row + mv.to_row) >> 1, mv.from_col)
            self._hash ^= _ZEP[self.en_passant_target[1]]

        # castling rights changes
        def _disable(cr_color, side):
            if self.castling_rights[cr_color][side]:
                self.castling_rights[cr_color][side] = False
                self._hash ^= _ZCASTLE[(cr_color, side)]

        if piece.kind is PieceType.KING:
            _disable(piece.color, 'K')
            _disable(piece.color, 'Q')
        elif piece.kind is PieceType.ROOK:
            if mv.from_col == 0: _disable(piece.color, 'Q')
            elif mv.from_col == 7: _disable(piece.color, 'K')
        if captured and captured.kind is PieceType.ROOK:
            if mv.to_col == 0: _disable(captured.color, 'Q')
            elif mv.to_col == 7: _disable(captured.color, 'K')

        # side to move
        self.turn = self.turn.opposite()

        # return undo information
        return (f, t, piece, captured,
                rook_from, rook_to, rook_piece,
                promoted_kind, ep_old,
                rights_snapshot, halfmove_old, hash_old)

    def pop(self, token):
        """
        Restore the state saved by the corresponding *push()*.
        """
        (f, t, piece, captured,
         rook_from, rook_to, rook_piece,
         promoted_kind, ep_old,
         rights_snapshot, halfmove_old, hash_old) = token

        # state
        self._hash           = hash_old
        self.halfmove_clock  = halfmove_old
        self.en_passant_target = ep_old
        (self.castling_rights[Color.WHITE]['K'],
         self.castling_rights[Color.WHITE]['Q'],
         self.castling_rights[Color.BLACK]['K'],
         self.castling_rights[Color.BLACK]['Q']) = rights_snapshot

        # undo move
        self.turn = self.turn.opposite()
        self.grid[f] = piece
        if promoted_kind != piece.kind:
            self.grid[t] = Piece(piece.color, promoted_kind)  # promoted dummy
        else:
            self.grid[t] = piece
        self.grid[t] = captured
        if rook_piece:
            self.grid[rook_from] = rook_piece
            self.grid[rook_to]   = None

    # ─────────────────────────────  Move generation  ───────────────────────────── #

    def legal_moves(self, color: Color):
        """
        Generate all *legal* moves without allocating new boards.
        Uses the fast push / pop that is already implemented.
        """
        for mv in self._pseudo_moves(color):
            token = self.push(mv)
            if not self._in_check(color):
                yield mv
            self.pop(token)

    # Pseudo‑legal = obeys piece movement but ignores check.
    def _pseudo_moves(self, color: Color, include_castling: bool = True):
        for r in range(8):
            for c in range(8):
                p = self.grid[self._sq(r, c)]
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
        piece = self.grid[self._sq(mv.from_row, mv.from_col)]
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
            self.grid[self._sq(*rook_from)] = None
            self.grid[self._sq(*rook_to)] = rook
            rook.has_moved = True

        # En‑passant capture (remove the pawn that was bypassed last move)
        if mv.is_en_passant:
            self.grid[self._sq(mv.from_row, mv.to_col)] = None

        # Move the actual piece
        self.grid[self._sq(mv.from_row, mv.from_col)] = None
        self.grid[self._sq(mv.to_row, mv.to_col)] = piece
        piece.has_moved = True

        # Promotion
        if piece.kind is PieceType.PAWN and mv.promotion:
            self.grid[self._sq(mv.to_row, mv.to_col)] = Piece(piece.color, mv.promotion, has_moved=True)

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

        # Time Selection
        time_group = QGroupBox("Time Control")
        time_layout = QVBoxLayout()
        self.cb_time = QComboBox()
        self.cb_time.addItems(["30 seconds", "1 minutes", "3 minutes", "5 minutes", "10 minutes"])
        time_layout.addWidget(self.cb_time)
        # Increment selection
        self.cb_increment = QComboBox()
        self.cb_increment.addItems(["+0s", "+1s", "+2s", "+5s"])
        time_layout.addWidget(self.cb_increment)
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # Enable/disable time selection based on mode
        def update_time_enabled():
            time_group.setEnabled(not self.rb_ai.isChecked())
        self.rb_ai.toggled.connect(update_time_enabled)
        update_time_enabled()

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

    @property
    def time_seconds(self):
        # Map combo box selection to seconds
        idx = self.cb_time.currentIndex()
        options = [30, 60, 180, 300, 600]
        return options[idx] if 0 <= idx < len(options) else 60

    @property
    def time_increment(self):
        idx = self.cb_increment.currentIndex()
        options = [0, 1, 2, 5]
        return options[idx] if 0 <= idx < len(options) else 0

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
                    # Add increment after move in 2P mode
                    mw = self.parentWidget()
                    while mw and not isinstance(mw, MainWindow):
                        mw = mw.parentWidget()
                    if mw and hasattr(mw, '_increment_clock') and mw.mode == "2p":
                        mw._increment_clock(self.board.turn.opposite())
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

# --- Evaluation Bar Widget ---
class EvalBarWidget(QWidget):
    def __init__(self, board: 'Board', parent=None):
        super().__init__(parent)
        self.board = board
        self.setFixedWidth(32)
        self.setMinimumHeight(8 * 72 + 32)  # match board height
        self.eval = 0.0
        self.setToolTip("Evaluation bar: 0.0")

    def set_eval(self, value: float):
        self.eval = value
        self.setToolTip(f"Evaluation: {value:+.2f}")
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        h = self.height()
        w = self.width()
        # Clamp eval to [-10, +10] for display
        eval_clamped = max(-10, min(10, self.eval))
        # Map eval to bar fill: +10 = all white, -10 = all black, 0 = half
        frac = 0.5 + 0.5 * (-eval_clamped / 10)
        white_h = int(h * (1 - frac))
        black_h = h - white_h
        # Draw white (top)
        p.fillRect(0, 0, w, white_h, QColor(240, 240, 240))
        # Draw black (bottom)
        p.fillRect(0, white_h, w, black_h, QColor(40, 40, 40))
        # Draw border
        p.setPen(QColor(80, 80, 80))
        p.drawRect(0, 0, w - 1, h - 1)
        # Optionally, draw a line at the midpoint
        p.setPen(QColor(120, 120, 120, 80))
        p.drawLine(0, h // 2, w, h // 2)

# MainWindow comes after BoardWidget
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Chess – PyQt6")
        self.board = Board()
        self.view = BoardWidget(self.board)
        self.evalbar = EvalBarWidget(self.board)
        # Chess clocks (5 minutes per player)
        self.white_time = 0.5 * 60.0  # seconds
        self.black_time = 0.5 * 60.0
        self.clock_running = False
        self.last_clock_update = None
        # Clock labels
        self.white_clock_label = QLabel(self._format_time(self.white_time))
        self.black_clock_label = QLabel(self._format_time(self.black_time))
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.white_clock_label.setFont(font)
        self.black_clock_label.setFont(font)
        self.white_clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.black_clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Layout: clocks and board/eval bar
        central = QWidget()
        vlayout = QVBoxLayout(central)
        vlayout.addWidget(self.black_clock_label)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.view)
        hlayout.addWidget(self.evalbar)
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.white_clock_label)
        self.setCentralWidget(central)
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
        # Periodically update eval bar
        timer_eval = QTimer(self)
        timer_eval.timeout.connect(self._refresh_evalbar)
        timer_eval.start(300)
        # Chess clock timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clocks)
        self.clock_timer.start(100)
        self.last_clock_update = QTimer().remainingTime()

    def _choose_mode_and_color(self):
        dlg = GameSetupDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.mode = dlg.mode
            if self.mode == "ai":
                self.ai_color = dlg.color
                self.board.turn = Color.WHITE if self.ai_color == Color.BLACK else Color.WHITE
                self.white_time = 0.5 * 60.0
                self.black_time = 0.5 * 60.0
                self.time_increment = 0
            else:
                self.ai_color = None
                t = dlg.time_seconds
                self.white_time = t
                self.black_time = t
                self.time_increment = dlg.time_increment
                self.white_clock_label.setText(self._format_time(self.white_time))
                self.black_clock_label.setText(self._format_time(self.black_time))
        else:
            self.mode = "2p"
            self.ai_color = None
            self.time_increment = 0

    def _refresh_status(self):
        if res := self.board.result():
            self.status.setText(res)
            self.clock_timer.stop()
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

    def _refresh_evalbar(self):
        # Show evaluation from white's perspective
        try:
            val = evaluate_board(self.board, Color.WHITE) / 100.0
        except Exception:
            val = 0.0
        self.evalbar.set_eval(val)

    def _format_time(self, t):
        t = max(0, int(t))
        m, s = divmod(t, 60)
        return f"{m:02}:{s:02}"

    def _update_clocks(self):
        if self.mode != "2p":
            return
        dt = 0.1  # seconds per tick
        if self.board.turn is Color.WHITE:
            self.white_time -= dt
            if self.white_time <= 0:
                self.white_time = 0
                self._end_game_on_time(Color.WHITE)
        else:
            self.black_time -= dt
            if self.black_time <= 0:
                self.black_time = 0
                self._end_game_on_time(Color.BLACK)
        self.white_clock_label.setText(self._format_time(self.white_time))
        self.black_clock_label.setText(self._format_time(self.black_time))

    def _increment_clock(self, color):
        if self.mode != "2p":
            return
        if color is Color.WHITE:
            self.white_time += self.time_increment
            self.white_clock_label.setText(self._format_time(self.white_time))
        else:
            self.black_time += self.time_increment
            self.black_clock_label.setText(self._format_time(self.black_time))

    def _end_game_on_time(self, color):
        winner = "Black" if color is Color.WHITE else "White"
        QMessageBox.information(self, "Time Out", f"{winner} wins on time!")
        # Optionally, stop the clock
        self.clock_timer.stop()

def main():
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method("spawn", force=True)
    main()
