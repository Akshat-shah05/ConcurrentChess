import { useState, useEffect, useRef } from 'react'
import { ChessBoard } from '@/components/ChessBoard'
import { ChessWebSocket } from '@/services/websocket'
import type { ChessMove, GameState } from '@/types/chess'
import { RotateCcw, Wifi, WifiOff, Users } from 'lucide-react'

export function MultiplayerGame() {
  const [gameState, setGameState] = useState<GameState | null>(null)
  const [legalMoves, setLegalMoves] = useState<ChessMove[]>([])
  const [selectedSquare, setSelectedSquare] = useState<[number, number] | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [playerColor, setPlayerColor] = useState<'white' | 'black' | null>(null)
  const [opponentConnected, setOpponentConnected] = useState(false)
  const wsRef = useRef<ChessWebSocket | null>(null)

  useEffect(() => {
    initializeWebSocket()
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect()
      }
    }
  }, [])

  const initializeWebSocket = () => {
    try {
      wsRef.current = new ChessWebSocket()
      
      // Set up event handlers
      wsRef.current.on('board_state', (message: any) => {
        setGameState({
          game_id: 'multiplayer',
          board: message.board,
          result: null
        })
      })

      wsRef.current.on('legal_moves', (message: any) => {
        setLegalMoves(message.moves || [])
      })

      wsRef.current.on('game_result', (message: any) => {
        setGameState(prev => prev ? {
          ...prev,
          result: message.result
        } : null)
      })

      wsRef.current.on('error', (message: any) => {
        setError(message.message || 'WebSocket error')
      })

      // Check connection status
      const checkConnection = () => {
        if (wsRef.current?.isConnected) {
          setConnected(true)
          setError(null)
          // Get initial board state
          wsRef.current?.getBoardState()
        } else {
          setConnected(false)
        }
      }

      // Check connection every 2 seconds
      const interval = setInterval(checkConnection, 2000)
      
      return () => clearInterval(interval)
    } catch (err) {
      setError('Failed to connect to multiplayer server')
      console.error('WebSocket initialization error:', err)
    }
  }

  const handleSquareClick = (row: number, col: number) => {
    if (!gameState || !connected || !isPlayerTurn()) return

    const piece = gameState.board.grid[row * 8 + col]
    if (piece && piece.color === gameState.board.turn) {
      setSelectedSquare([row, col])
      wsRef.current?.getLegalMoves()
    }
  }

  const handleMove = (move: ChessMove) => {
    if (!gameState || !connected || !isPlayerTurn()) return

    setSelectedSquare(null)
    setLegalMoves([])
    wsRef.current?.makeMove(move)
  }

  const isPlayerTurn = () => {
    if (!gameState || !playerColor) return false
    return gameState.board.turn === playerColor
  }

  const resetGame = () => {
    setGameState(null)
    setLegalMoves([])
    setSelectedSquare(null)
    setError(null)
    setPlayerColor(null)
    wsRef.current?.getBoardState()
  }

  const joinAsWhite = () => {
    setPlayerColor('white')
    setOpponentConnected(true)
  }

  const joinAsBlack = () => {
    setPlayerColor('black')
    setOpponentConnected(true)
  }

  if (!connected) {
    return (
      <div className="text-center">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <div className="flex items-center justify-center space-x-2">
            <WifiOff className="w-5 h-5" />
            <span>Not connected to multiplayer server</span>
          </div>
        </div>
        <p className="text-gray-600 mb-4">
          Make sure the backend is running and the WebSocket server is active on port 8766.
        </p>
        <button onClick={initializeWebSocket} className="btn-primary">
          Try Connecting Again
        </button>
      </div>
    )
  }

  if (!playerColor) {
    return (
      <div className="max-w-2xl mx-auto text-center">
        <h1 className="text-3xl font-bold text-chess-dark mb-8">Multiplayer Chess</h1>
        
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="flex items-center justify-center space-x-2 mb-6">
            <Wifi className="w-5 h-5 text-green-600" />
            <span className="text-green-600 font-medium">Connected to server</span>
          </div>
          
          <h2 className="text-xl font-semibold mb-6">Choose your color:</h2>
          
          <div className="flex justify-center space-x-4">
            <button
              onClick={joinAsWhite}
              className="bg-white text-black border-2 border-black px-8 py-4 rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              <div className="text-2xl mb-2">♔</div>
              <div>Play as White</div>
            </button>
            
            <button
              onClick={joinAsBlack}
              className="bg-black text-white border-2 border-black px-8 py-4 rounded-lg font-medium hover:bg-gray-800 transition-colors"
            >
              <div className="text-2xl mb-2">♚</div>
              <div>Play as Black</div>
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!gameState) {
    return (
      <div className="text-center">
        <div className="flex items-center justify-center space-x-2 mb-4">
          <Wifi className="w-5 h-5 text-green-600" />
          <span className="text-green-600">Connected</span>
        </div>
        <p>Waiting for game to start...</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-chess-dark mb-4">Multiplayer Chess</h1>
        
        {/* Status indicators */}
        <div className="flex justify-center items-center space-x-6 mb-6">
          <div className="flex items-center space-x-2">
            <Wifi className={`w-4 h-4 ${connected ? 'text-green-600' : 'text-red-600'}`} />
            <span className="text-sm">{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-blue-600" />
            <span className="text-sm">
              Playing as {playerColor === 'white' ? 'White ♔' : 'Black ♚'}
            </span>
          </div>
          
          <button 
            onClick={resetGame} 
            className="btn-secondary inline-flex items-center space-x-2"
          >
            <RotateCcw className="w-4 h-4" />
            <span>New Game</span>
          </button>
        </div>

        {/* Turn indicator */}
        {!gameState.result && (
          <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-2 rounded mb-4">
            <span className="font-medium">
              {isPlayerTurn() ? 'Your turn' : 'Opponent\'s turn'}
            </span>
          </div>
        )}
      </div>

      {/* Chess Board */}
      <div className="flex justify-center">
        <ChessBoard
          board={gameState.board}
          legalMoves={legalMoves}
          selectedSquare={selectedSquare}
          onSquareClick={handleSquareClick}
          onMove={handleMove}
          isPlayerTurn={isPlayerTurn()}
          gameResult={gameState.result}
        />
      </div>

      {/* Game info */}
      <div className="mt-8 text-center">
        <div className="bg-white rounded-lg shadow p-4 inline-block">
          <p className="text-sm text-gray-600">Move: {gameState.board.fullmove_number}</p>
          <p className="text-sm text-gray-600">Half-move clock: {gameState.board.halfmove_clock}</p>
        </div>
      </div>
    </div>
  )
} 