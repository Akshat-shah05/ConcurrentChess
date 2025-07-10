import { useState, useEffect } from 'react'
import { ChessBoard } from '@/components/ChessBoard'
import { EvaluationBar } from '@/components/EvaluationBar'
import { chessAPI } from '@/services/api'
import type { ChessMove, GameState } from '@/types/chess'
import { RotateCcw, Settings, Loader2, Clock, Trophy, AlertCircle } from 'lucide-react'

interface MoveHistory {
  move: ChessMove
  result: string | null
  timestamp: Date
}

export function AIGame() {
  const [gameState, setGameState] = useState<GameState | null>(null)
  const [legalMoves, setLegalMoves] = useState<ChessMove[]>([])
  const [selectedSquare, setSelectedSquare] = useState<[number, number] | null>(null)
  const [loading, setLoading] = useState(false)
  const [aiThinking, setAiThinking] = useState(false)
  const [aiDepth, setAiDepth] = useState(4)
  const [error, setError] = useState<string | null>(null)
  const [moveHistory, setMoveHistory] = useState<MoveHistory[]>([])
  const [lastMove, setLastMove] = useState<ChessMove | null>(null)

  // Initialize game
  useEffect(() => {
    initializeGame()
  }, [])

  const initializeGame = async () => {
    try {
      setLoading(true)
      setError(null)
      setMoveHistory([])
      setLastMove(null)
      
      const { game_id } = await chessAPI.createGame()
      const state = await chessAPI.getGameState(game_id)
      setGameState(state)
      
      // Get legal moves for white
      const movesResponse = await chessAPI.getLegalMoves(game_id)
      setLegalMoves(movesResponse.moves)
    } catch (err) {
      setError('Failed to initialize game. Please check if the backend is running.')
      console.error('Game initialization error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSquareClick = async (row: number, col: number) => {
    if (!gameState || aiThinking) return

    const piece = gameState.board.grid[row * 8 + col]
    console.log('Square clicked:', row, col, 'Piece:', piece)
    
    if (piece && piece.color === gameState.board.turn) {
      setSelectedSquare([row, col])
      
      try {
        const movesResponse = await chessAPI.getLegalMoves(gameState.game_id)
        const filteredMoves = movesResponse.moves.filter(move => 
          move.from_row === row && move.from_col === col
        )
        console.log('Legal moves for selected piece:', filteredMoves)
        setLegalMoves(filteredMoves)
      } catch (err) {
        console.error('Failed to get legal moves:', err)
        setError('Failed to get legal moves')
      }
    }
  }

  const handleMove = async (move: ChessMove) => {
    if (!gameState || aiThinking) return

    console.log('Making move:', move)

    try {
      setAiThinking(true)
      setSelectedSquare(null)
      setLegalMoves([])

      // Make player's move
      console.log('Sending move to backend:', move)
      const updatedState = await chessAPI.makeMove(gameState.game_id, move)
      console.log('Move response:', updatedState)
      setGameState(updatedState)
      setLastMove(move)

      // Add to move history
      setMoveHistory(prev => [...prev, {
        move,
        result: updatedState.result,
        timestamp: new Date()
      }])

      // Check if game is over
      if (updatedState.result) {
        console.log('Game over:', updatedState.result)
        return
      }

      // Get AI move
      console.log('Requesting AI move...')
      const aiResponse = await chessAPI.getAIMove(gameState.game_id, aiDepth)
      console.log('AI move response:', aiResponse)
      setGameState({
        game_id: gameState.game_id,
        board: aiResponse.board,
        result: aiResponse.result
      })
      setLastMove(aiResponse.move)

      // Add AI move to history
      setMoveHistory(prev => [...prev, {
        move: aiResponse.move,
        result: aiResponse.result,
        timestamp: new Date()
      }])

      // Get legal moves for next player turn
      if (!aiResponse.result) {
        const movesResponse = await chessAPI.getLegalMoves(gameState.game_id)
        setLegalMoves(movesResponse.moves)
      }
    } catch (err) {
      console.error('Move error:', err)
      setError(`Failed to make move: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setAiThinking(false)
    }
  }

  const resetGame = () => {
    setGameState(null)
    setLegalMoves([])
    setSelectedSquare(null)
    setError(null)
    setMoveHistory([])
    setLastMove(null)
    initializeGame()
  }

  const formatMove = (move: ChessMove) => {
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    const ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    const from = `${files[move.from_col]}${ranks[move.from_row]}`
    const to = `${files[move.to_col]}${ranks[move.to_row]}`
    
    return `${from}-${to}${move.promotion ? `=${move.promotion}` : ''}`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>Initializing game...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <div className="flex items-center justify-center space-x-2">
            <AlertCircle className="w-5 h-5" />
            <div>
              <p className="font-bold">Error</p>
              <p>{error}</p>
            </div>
          </div>
        </div>
        <button onClick={resetGame} className="btn-primary">
          Try Again
        </button>
      </div>
    )
  }

  if (!gameState) {
    return (
      <div className="text-center">
        <p>Loading game...</p>
      </div>
    )
  }

  const isPlayerTurn = gameState.board.turn === 'white'

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-chess-dark mb-4">Play vs AI</h1>
        
        {/* Controls */}
        <div className="flex justify-center items-center space-x-4 mb-6">
          <button 
            onClick={resetGame} 
            className="btn-secondary inline-flex items-center space-x-2"
            disabled={aiThinking}
          >
            <RotateCcw className="w-4 h-4" />
            <span>New Game</span>
          </button>
          
          <div className="flex items-center space-x-2">
            <Settings className="w-4 h-4" />
            <label htmlFor="ai-depth" className="text-sm font-medium">AI Depth:</label>
            <select
              id="ai-depth"
              value={aiDepth}
              onChange={(e) => setAiDepth(Number(e.target.value))}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
              disabled={aiThinking}
            >
              <option value={2}>Easy (2)</option>
              <option value={4}>Medium (4)</option>
              <option value={6}>Hard (6)</option>
            </select>
          </div>
        </div>

        {/* AI thinking indicator - always present to prevent layout shift */}
        <div className="h-12 mb-6 flex items-center justify-center">
          <div className={`bg-blue-100 border border-blue-400 text-blue-700 px-4 py-2 rounded transition-all duration-300 ${aiThinking ? 'opacity-100' : 'opacity-0'}`}>
            <div className="flex items-center justify-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>AI is thinking...</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row justify-center items-start w-full gap-8">
        {/* Chess Board */}
        <div className="flex justify-center items-center min-h-[600px]">
          <ChessBoard
            board={gameState.board}
            legalMoves={legalMoves}
            selectedSquare={selectedSquare}
            onSquareClick={handleSquareClick}
            onMove={handleMove}
            isPlayerTurn={isPlayerTurn}
            gameResult={gameState.result}
            lastMove={lastMove}
          />
        </div>
        {/* Sidebar: Eval bar + Info blocks */}
        <div className="flex flex-row items-center min-h-[600px]">
          {/* Evaluation Bar - centered vertically */}
          <div className="flex flex-col justify-center items-center h-full">
            <EvaluationBar gameId={gameState.game_id} />
          </div>
          {/* Info blocks stacked vertically, wide, centered */}
          <div className="flex flex-col justify-center items-center ml-8 w-[340px] max-w-full space-y-6">
            {/* Game status */}
            <div className="bg-white rounded-lg shadow-lg p-4 w-full">
              <h3 className="text-lg font-semibold mb-3 flex items-center">
                <Clock className="w-5 h-5 mr-2" />
                Game Info
              </h3>
              <div className="space-y-2 text-sm">
                <p><span className="font-medium">Move:</span> {gameState.board.fullmove_number}</p>
                <p><span className="font-medium">Turn:</span> {gameState.board.turn === 'white' ? 'White' : 'Black'}</p>
                {gameState.result && (
                  <div className="mt-3 p-2 bg-yellow-100 rounded">
                    <div className="flex items-center">
                      <Trophy className="w-4 h-4 mr-2" />
                      <span className="font-medium">{gameState.result}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Last move */}
            {lastMove && (
              <div className="bg-white rounded-lg shadow-lg p-4 w-full">
                <h3 className="text-lg font-semibold mb-3">Last Move</h3>
                <div className="bg-gray-100 rounded p-3 font-mono text-sm">
                  {formatMove(lastMove)}
                </div>
              </div>
            )}

            {/* Move history */}
            {moveHistory.length > 0 && (
              <div className="bg-white rounded-lg shadow-lg p-4 w-full">
                <h3 className="text-lg font-semibold mb-3">Move History</h3>
                <div className="max-h-48 overflow-y-auto space-y-1 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100 pr-2">
                  {moveHistory.map((history, index) => (
                    <div key={index} className="flex justify-between items-center text-sm">
                      <span className="font-mono">{formatMove(history.move)}</span>
                      <span className="text-gray-500 text-xs">
                        {history.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 