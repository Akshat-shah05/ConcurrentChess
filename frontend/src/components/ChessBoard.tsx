import { useState } from 'react'
import type { ChessBoard, ChessPiece, ChessMove } from '@/types/chess'
import { ChessPiece as ChessPieceComponent } from '@/components/ChessPiece'

interface ChessBoardProps {
  board: ChessBoard
  legalMoves: ChessMove[]
  selectedSquare: [number, number] | null
  onSquareClick: (row: number, col: number) => void
  onMove: (move: ChessMove) => void
  isPlayerTurn: boolean
  gameResult: string | null
  lastMove?: ChessMove | null
}

export function ChessBoard({ 
  board, 
  legalMoves, 
  selectedSquare, 
  onSquareClick, 
  onMove, 
  isPlayerTurn,
  gameResult,
  lastMove
}: ChessBoardProps) {
  const [promotionMove, setPromotionMove] = useState<ChessMove | null>(null)

  const getSquareClass = (row: number, col: number) => {
    const isLight = (row + col) % 2 === 0
    let className = `chess-square ${isLight ? 'chess-square-light' : 'chess-square-dark'}`

    // Highlight selected square
    if (selectedSquare && selectedSquare[0] === row && selectedSquare[1] === col) {
      className += ' chess-square-selected'
    }

    // Highlight legal moves
    const isLegalMove = legalMoves.some(move => 
      move.from_row === selectedSquare?.[0] && 
      move.from_col === selectedSquare?.[1] && 
      move.to_row === row && 
      move.to_col === col
    )

    if (isLegalMove) {
      const piece = board.grid[row * 8 + col]
      if (piece) {
        className += ' chess-square-capture'
      } else {
        className += ' chess-square-move'
      }
    }

    // Highlight last move
    if (lastMove && (
      (lastMove.from_row === row && lastMove.from_col === col) ||
      (lastMove.to_row === row && lastMove.to_col === col)
    )) {
      className += ' chess-square-last-move'
    }

    return className
  }

  const getPiece = (row: number, col: number): ChessPiece | null => {
    return board.grid[row * 8 + col]
  }

  const handleSquareClick = (row: number, col: number) => {
    if (gameResult || !isPlayerTurn) return

    const piece = getPiece(row, col)
    
    // If clicking on a piece of the current player's color
    if (piece && piece.color === board.turn) {
      onSquareClick(row, col)
      return
    }

    // If a square is selected and clicking on a different square
    if (selectedSquare) {
      const move = legalMoves.find(m => 
        m.from_row === selectedSquare[0] && 
        m.from_col === selectedSquare[1] && 
        m.to_row === row && 
        m.to_col === col
      )

      if (move) {
        // Check if this is a pawn promotion
        const fromPiece = getPiece(move.from_row, move.from_col)
        if (fromPiece?.kind === 'P' && (row === 0 || row === 7)) {
          setPromotionMove(move)
        } else {
          onMove(move)
        }
      }
    }
  }

  const handlePromotion = (promotionType: string) => {
    if (promotionMove) {
      const moveWithPromotion = {
        ...promotionMove,
        promotion: promotionType
      }
      onMove(moveWithPromotion)
      setPromotionMove(null)
    }
  }

  const renderPromotionModal = () => {
    if (!promotionMove) return null

    const promotionPieces = [
      { type: 'Q', name: 'Queen', symbol: '♕' },
      { type: 'R', name: 'Rook', symbol: '♖' },
      { type: 'B', name: 'Bishop', symbol: '♗' },
      { type: 'N', name: 'Knight', symbol: '♘' }
    ]

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 shadow-xl">
          <h3 className="text-lg font-semibold mb-4 text-center">Choose promotion piece:</h3>
          <div className="flex space-x-4">
            {promotionPieces.map(({ type, name, symbol }) => (
              <button
                key={type}
                onClick={() => handlePromotion(type)}
                className="flex flex-col items-center p-4 border-2 border-gray-200 rounded-lg hover:border-chess-dark hover:bg-gray-50 transition-all duration-200 transform hover:scale-105"
              >
                <span className="text-4xl mb-2">{symbol}</span>
                <span className="text-sm font-medium">{name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const renderCoordinates = () => {
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    const ranks = ['8', '7', '6', '5', '4', '3', '2', '1']

    return (
      <>
        {/* File coordinates (bottom) */}
        <div className="flex justify-center mt-2">
          {files.map((file, index) => (
            <div key={file} className="w-12 md:w-16 lg:w-20 text-center text-sm font-medium text-gray-600">
              {file}
            </div>
          ))}
        </div>
        
        {/* Rank coordinates (left side) */}
        <div className="absolute left-2 top-0 bottom-0 flex flex-col justify-center">
          {ranks.map((rank, index) => (
            <div key={rank} className="h-12 md:h-16 lg:h-20 flex items-center justify-center text-sm font-medium text-gray-600">
              {rank}
            </div>
          ))}
        </div>
      </>
    )
  }

  return (
    <div className="flex flex-col items-center">
      {/* Game status */}
      {gameResult && (
        <div className="mb-6 p-4 bg-gradient-to-r from-yellow-100 to-orange-100 border border-yellow-400 rounded-lg shadow-lg">
          <h3 className="text-xl font-bold text-yellow-800 text-center">{gameResult}</h3>
        </div>
      )}

      {/* Turn indicator */}
      {!gameResult && (
        <div className="mb-6 p-4 bg-white rounded-lg shadow-lg border-2 border-gray-200">
          <div className="flex items-center justify-center space-x-3">
            <span className="text-lg font-medium">
              {isPlayerTurn ? 'Your turn' : 'AI is thinking...'}
            </span>
            <div className={`w-6 h-6 rounded-full border-2 ${board.turn === 'white' ? 'bg-white border-black' : 'bg-black border-white'}`}></div>
          </div>
        </div>
      )}

      {/* Chess board container */}
      <div className="relative">
        {/* Board with coordinates */}
        <div className="border-4 border-chess-dark rounded-lg overflow-hidden shadow-2xl bg-chess-dark">
          <div className="grid grid-cols-8 relative">
            {Array.from({ length: 8 }, (_, row) =>
              Array.from({ length: 8 }, (_, col) => {
                const squareIndex = row * 8 + col
                const piece = board.grid[squareIndex]
                
                return (
                  <div
                    key={`${row}-${col}`}
                    className={getSquareClass(row, col)}
                    onClick={() => handleSquareClick(row, col)}
                  >
                    {piece && (
                      <ChessPieceComponent piece={piece} />
                    )}
                    
                    {/* Move indicators */}
                    {legalMoves.some(move => 
                      move.from_row === selectedSquare?.[0] && 
                      move.from_col === selectedSquare?.[1] && 
                      move.to_row === row && 
                      move.to_col === col
                    ) && (
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        {board.grid[squareIndex] ? (
                          // Capture indicator
                          <div className="w-8 h-8 md:w-10 md:h-10 lg:w-12 lg:h-12 border-4 border-red-500 rounded-full opacity-80"></div>
                        ) : (
                          // Move indicator
                          <div className="w-3 h-3 md:w-4 md:h-4 lg:w-5 lg:h-5 bg-blue-500 rounded-full opacity-80"></div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>
        </div>
        
        {/* Coordinates */}
        {renderCoordinates()}
      </div>

      {/* Promotion modal */}
      {renderPromotionModal()}
    </div>
  )
} 