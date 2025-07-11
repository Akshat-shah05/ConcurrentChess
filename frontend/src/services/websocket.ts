import type { 
  WebSocketMessage, 
  ChessMove 
} from '@/types/chess'

const SOCKET_HOST = 'localhost'
const SOCKET_PORT = 8766

export class ChessWebSocket {
  private ws: WebSocket | null = null
  private messageHandlers: Map<string, ((data: any) => void)[]> = new Map()
  private gameId: string | null = null

  constructor() {
    this.connect()
  }

  public get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  private connect() {
    try {
      this.ws = new WebSocket(`ws://${SOCKET_HOST}:${SOCKET_PORT}/ws`)
      
      this.ws.onopen = () => {
        console.log('WebSocket connected')
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        // Attempt to reconnect after 5 seconds
        setTimeout(() => this.connect(), 5000)
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error)
    }
  }

  private handleMessage(message: WebSocketMessage) {
    const handlers = this.messageHandlers.get(message.type) || []
    handlers.forEach(handler => handler(message))
  }

  public on(event: string, handler: (data: any) => void) {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, [])
    }
    this.messageHandlers.get(event)!.push(handler)
  }

  public off(event: string, handler: (data: any) => void) {
    const handlers = this.messageHandlers.get(event) || []
    const index = handlers.indexOf(handler)
    if (index > -1) {
      handlers.splice(index, 1)
    }
  }

  public send(message: WebSocketMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocket is not connected')
    }
  }

  // Game management methods
  public createGame() {
    this.send({ type: 'create_game' })
  }

  public getGames() {
    this.send({ type: 'get_games' })
  }

  public joinGame(gameId: string) {
    this.gameId = gameId
    this.send({ type: 'join', game_id: gameId })
  }

  // Chess-specific methods
  public getBoardState(gameId: string = this.gameId || 'default') {
    this.send({ type: 'board_state', game_id: gameId })
  }

  public getLegalMoves(gameId: string = this.gameId || 'default') {
    this.send({ type: 'legal_moves', game_id: gameId })
  }

  public getEvaluation(gameId: string = this.gameId || 'default') {
    this.send({ type: 'evaluation', game_id: gameId })
  }

  public makeMove(move: ChessMove, gameId: string = this.gameId || 'default') {
    this.send({ type: 'move', game_id: gameId, move })
  }

  public getAIMove(depth: number = 4, gameId: string = this.gameId || 'default') {
    this.send({ type: 'ai_move', game_id: gameId, depth })
  }

  public getCurrentGameId(): string | null {
    return this.gameId
  }

  public disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.gameId = null
  }
} 