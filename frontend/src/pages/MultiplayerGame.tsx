import { useState, useEffect, useRef } from 'react'
import { ChessBoard } from '@/components/ChessBoard'
import { ChessWebSocket } from '@/services/websocket'
import type { ChessMove, GameState } from '@/types/chess'
import { RotateCcw, Wifi, WifiOff, Users, Loader2, Plus, Play, ArrowLeft } from 'lucide-react'

interface GameInfo {
  game_id: string
  players: number
  max_players: number
  status: 'waiting' | 'playing'
}

export function MultiplayerGame() {
  const [gameState, setGameState] = useState<GameState | null>(null)
  const [legalMoves, setLegalMoves] = useState<ChessMove[]>([])
  const [selectedSquare, setSelectedSquare] = useState<[number, number] | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [playerColor, setPlayerColor] = useState<'white' | 'black' | null>(null)
  const [opponentConnected, setOpponentConnected] = useState(false)
  const [availableGames, setAvailableGames] = useState<GameInfo[]>([])
  const [currentGameId, setCurrentGameId] = useState<string | null>(null)
  const [gameStarted, setGameStarted] = useState(false)
  const [showLobby, setShowLobby] = useState(true)
  const wsRef = useRef<ChessWebSocket | null>(null)
  const [connecting, setConnecting] = useState(true)

  useEffect(() => {
    setConnecting(true)
    const timeout = setTimeout(() => setConnecting(false), 1000)
    return () => clearTimeout(timeout)
  }, [])

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
          game_id: currentGameId || 'multiplayer',
          board: message.board,
          result: null
        })
      })

      wsRef.current.on('legal_moves', (message: any) => {
        console.log('Received legal moves:', message.moves)
        setLegalMoves(message.moves || [])
      })

      wsRef.current.on('game_result', (message: any) => {
        setGameState(prev => prev ? {
          ...prev,
          result: message.result
        } : null)
      })

      wsRef.current.on('player_assignment', (message: any) => {
        console.log('Player assigned color:', message.color)
        setPlayerColor(message.color)
        setShowLobby(false)
        setGameStarted(true)
      })

      wsRef.current.on('player_joined', (message: any) => {
        console.log('Player joined:', message)
        setOpponentConnected(true)
        if (message.total_players >= 2) {
          setGameStarted(true)
        }
      })

      wsRef.current.on('game_started', (message: any) => {
        console.log('Game started:', message)
        setGameStarted(true)
      })

      wsRef.current.on('player_disconnected', (message: any) => {
        console.log('Player disconnected:', message)
        setOpponentConnected(false)
        setError('Opponent disconnected')
      })

      wsRef.current.on('game_created', (message: any) => {
        console.log('Game created:', message)
        setCurrentGameId(message.game_id)
        // Auto-join the created game
        wsRef.current?.joinGame(message.game_id)
      })

      wsRef.current.on('game_list', (message: any) => {
        console.log('Game list received:', message.games)
        setAvailableGames(message.games || [])
      })

      wsRef.current.on('error', (message: any) => {
        console.error('WebSocket error:', message)
        setError(message.message || 'WebSocket error')
      })

      // Check connection status
      const checkConnection = () => {
        if (wsRef.current?.isConnected) {
          setConnected(true)
          setError(null)
          // Get available games
          wsRef.current?.getGames()
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
    if (!gameState || !connected || !isPlayerTurn()) {
      console.log('Square click ignored:', { row, col, gameState: !!gameState, connected, isPlayerTurn: isPlayerTurn() })
      return
    }

    const piece = gameState.board.grid[row * 8 + col]
    console.log('Square clicked:', { row, col, piece, playerColor, boardTurn: gameState.board.turn })
    
    // In multiplayer, check if the piece belongs to the current player
    if (piece && piece.color === playerColor) {
      console.log('Selecting piece:', piece)
      setSelectedSquare([row, col])
      wsRef.current?.getLegalMoves()
    } else {
      console.log('Piece not selectable:', { pieceColor: piece?.color, playerColor })
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

  const createGame = () => {
    wsRef.current?.createGame()
  }

  const joinGame = (gameId: string) => {
    setCurrentGameId(gameId)
    wsRef.current?.joinGame(gameId)
  }

  const backToLobby = () => {
    setShowLobby(true)
    setGameState(null)
    setLegalMoves([])
    setSelectedSquare(null)
    setError(null)
    setPlayerColor(null)
    setCurrentGameId(null)
    setGameStarted(false)
    setOpponentConnected(false)
    wsRef.current?.disconnect()
    initializeWebSocket()
  }

  const resetGame = () => {
    setGameState(null)
    setLegalMoves([])
    setSelectedSquare(null)
    setError(null)
    setPlayerColor(null)
    setCurrentGameId(null)
    setGameStarted(false)
    setOpponentConnected(false)
    setShowLobby(true)
    wsRef.current?.disconnect()
    initializeWebSocket()
  }

  if (connecting) {
    return (
      <div className="text-center">
        <div className="flex items-center justify-center space-x-2 mb-4">
          <Wifi className="w-5 h-5 text-blue-600 animate-spin" />
          <span className="text-blue-600">Connecting to multiplayer server...</span>
        </div>
      </div>
    )
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

  // Show lobby if not in a game
  if (showLobby) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-chess-dark mb-4">Multiplayer Chess</h1>
          
          <div className="flex items-center justify-center space-x-2 mb-6">
            <Wifi className="w-5 h-5 text-green-600" />
            <span className="text-green-600 font-medium">Connected to server</span>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Create Game */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Create New Game</h2>
            <p className="text-gray-600 mb-6">
              Start a new game and wait for another player to join.
            </p>
            <button
              onClick={createGame}
              className="btn-primary inline-flex items-center space-x-2"
            >
              <Plus className="w-5 h-5" />
              <span>Create Game</span>
            </button>
          </div>

          {/* Join Game */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Join Existing Game</h2>
            <p className="text-gray-600 mb-6">
              Join a game that's waiting for players.
            </p>
            
            {availableGames.length === 0 ? (
              <p className="text-gray-500 italic">No games available</p>
            ) : (
              <div className="space-y-2">
                {availableGames.map((game) => (
                  <div
                    key={game.game_id}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                  >
                    <div>
                      <span className="font-medium">Game {game.game_id}</span>
                      <div className="text-sm text-gray-500">
                        {game.players}/{game.max_players} players • {game.status}
                      </div>
                    </div>
                    <button
                      onClick={() => joinGame(game.game_id)}
                      disabled={game.status === 'playing'}
                      className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {game.status === 'playing' ? 'Full' : 'Join'}
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            <button
              onClick={() => wsRef.current?.getGames()}
              className="btn-secondary mt-4 inline-flex items-center space-x-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Show waiting screen if joined but game hasn't started
  if (!gameStarted) {
    return (
      <div className="max-w-2xl mx-auto text-center">
        <h1 className="text-3xl font-bold text-chess-dark mb-8">Waiting for Players</h1>
        
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="flex items-center justify-center space-x-2 mb-6">
            <Wifi className="w-5 h-5 text-green-600" />
            <span className="text-green-600 font-medium">Connected to server</span>
          </div>
          
          <h2 className="text-xl font-semibold mb-4">Game ID: {currentGameId}</h2>
          
          <div className="flex items-center justify-center space-x-2 mb-6">
            <Users className="w-5 h-5 text-blue-600" />
            <span className="text-blue-600">
              {opponentConnected ? 'Opponent joined!' : 'Waiting for opponent...'}
            </span>
          </div>
          
          <p className="text-gray-600 mb-6">
            Share this game ID with another player to start the game.
          </p>
          
          <button 
            onClick={backToLobby} 
            className="btn-secondary inline-flex items-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Lobby</span>
          </button>
        </div>
      </div>
    )
  }

  // Show game if started
  if (!gameState) {
    return (
      <div className="text-center">
        <div className="flex items-center justify-center space-x-2 mb-4">
          <Wifi className="w-5 h-5 text-green-600" />
          <span className="text-green-600">Connected</span>
        </div>
        <p>Loading game...</p>
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
          
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Game: {currentGameId}</span>
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

        {/* Error display */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-4">
            {error}
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
          playerColor={playerColor}
          isMultiplayer={true}
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