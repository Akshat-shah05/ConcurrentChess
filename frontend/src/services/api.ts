import axios from 'axios'
import type { GameState, LegalMovesResponse, AIMoveResponse, ChessMove, ChessBoard, ChessPiece } from '@/types/chess'

const API_BASE = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Conversion functions for backend data format
const convertBackendPiece = (piece: any): ChessPiece | null => {
  if (!piece) return null
  
  return {
    color: piece.color === 0 ? 'white' : 'black',
    kind: piece.kind,
    has_moved: piece.has_moved
  }
}

const convertBackendBoard = (board: any): ChessBoard => {
  return {
    grid: board.grid.map(convertBackendPiece),
    turn: board.turn === 0 ? 'white' : 'black',
    en_passant_target: board.en_passant_target,
    castling_rights: board.castling_rights,
    halfmove_clock: board.halfmove_clock,
    fullmove_number: board.fullmove_number
  }
}

const convertFrontendMove = (move: ChessMove): any => {
  return {
    from_row: move.from_row,
    from_col: move.from_col,
    to_row: move.to_row,
    to_col: move.to_col,
    promotion: move.promotion,
    is_en_passant: move.is_en_passant,
    is_castling: move.is_castling
  }
}

export const chessAPI = {
  // Create a new game
  createGame: async (): Promise<{ game_id: string; status: string }> => {
    try {
      const response = await api.post('/api/games')
      return response.data
    } catch (error) {
      console.error('createGame error:', error)
      throw error
    }
  },

  // Get game state
  getGameState: async (gameId: string): Promise<GameState> => {
    try {
      const response = await api.get(`/api/games/${gameId}`)
      const data = response.data
      return {
        game_id: data.game_id,
        board: convertBackendBoard(data.board),
        result: data.result
      }
    } catch (error) {
      console.error('getGameState error:', error)
      throw error
    }
  },

  // Get legal moves
  getLegalMoves: async (gameId: string): Promise<LegalMovesResponse> => {
    try {
      const response = await api.get(`/api/games/${gameId}/legal_moves`)
      return response.data
    } catch (error) {
      console.error('getLegalMoves error:', error)
      throw error
    }
  },

  // Make a move
  makeMove: async (gameId: string, move: ChessMove): Promise<GameState> => {
    try {
      const moveData = convertFrontendMove(move)
      console.log('Sending move data:', moveData)
      const response = await api.post(`/api/games/${gameId}/move`, moveData)
      const data = response.data
      return {
        game_id: data.game_id,
        board: convertBackendBoard(data.board),
        result: data.result
      }
    } catch (error) {
      console.error('makeMove error:', error)
      throw error
    }
  },

  // Get AI move
  getAIMove: async (gameId: string, depth: number = 4): Promise<AIMoveResponse> => {
    try {
      const response = await api.post(`/api/games/${gameId}/ai_move?depth=${depth}`)
      const data = response.data
      return {
        game_id: data.game_id,
        move: data.move,
        board: convertBackendBoard(data.board),
        result: data.result
      }
    } catch (error) {
      console.error('getAIMove error:', error)
      throw error
    }
  },

  // Get board evaluation
  getEvaluation: async (gameId: string): Promise<{ game_id: string; evaluation: number }> => {
    try {
      const response = await api.get(`/api/games/${gameId}/evaluation`)
      return response.data
    } catch (error) {
      console.error('getEvaluation error:', error)
      throw error
    }
  },

  // List all games
  listGames: async (): Promise<{ games: string[] }> => {
    try {
      const response = await api.get('/api/games')
      return response.data
    } catch (error) {
      console.error('listGames error:', error)
      throw error
    }
  },
} 