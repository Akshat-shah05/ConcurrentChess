export interface ChessPiece {
  color: 'white' | 'black'
  kind: 'P' | 'N' | 'B' | 'R' | 'Q' | 'K'
  has_moved: boolean
}

export interface ChessBoard {
  grid: (ChessPiece | null)[]
  turn: 'white' | 'black'
  en_passant_target: [number, number] | null
  castling_rights: {
    white: { K: boolean; Q: boolean }
    black: { K: boolean; Q: boolean }
  }
  halfmove_clock: number
  fullmove_number: number
}

export interface ChessMove {
  from_row: number
  from_col: number
  to_row: number
  to_col: number
  promotion: string | null
  is_en_passant: boolean
  is_castling: boolean
}

export interface GameState {
  game_id: string
  board: ChessBoard
  result: string | null
}

export interface LegalMovesResponse {
  game_id: string
  moves: ChessMove[]
}

export interface AIMoveResponse {
  game_id: string
  move: ChessMove
  board: ChessBoard
  result: string | null
}

export interface GameResult {
  result: string
  board: ChessBoard
}

// WebSocket message types
export interface WebSocketMessage {
  type: string
  [key: string]: any
} 