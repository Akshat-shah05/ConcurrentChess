import { Link } from 'react-router-dom'
import { Bot, Users, Play } from 'lucide-react'

export function Home() {
  return (
    <div className="text-center">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl md:text-6xl font-bold text-chess-dark mb-6">
          Welcome to Concurrent Chess
        </h1>
        <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
          Experience the power of concurrent chess with AI opponents and real-time multiplayer matches.
        </p>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* AI Mode */}
          <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200 hover:shadow-xl transition-shadow">
            <div className="flex justify-center mb-6">
              <div className="bg-blue-100 p-4 rounded-full">
                <Bot className="w-12 h-12 text-blue-600" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-chess-dark mb-4">Play vs AI</h2>
            <p className="text-gray-600 mb-6">
              Challenge our advanced chess AI with configurable difficulty levels. 
              Perfect for practice and improving your game.
            </p>
            <Link to="/ai" className="btn-primary inline-flex items-center space-x-2">
              <Play className="w-5 h-5" />
              <span>Start AI Game</span>
            </Link>
          </div>

          {/* Multiplayer Mode */}
          <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200 hover:shadow-xl transition-shadow">
            <div className="flex justify-center mb-6">
              <div className="bg-green-100 p-4 rounded-full">
                <Users className="w-12 h-12 text-green-600" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-chess-dark mb-4">Multiplayer</h2>
            <p className="text-gray-600 mb-6">
              Play against other players in real-time using WebSocket connections. 
              Experience the thrill of live chess matches.
            </p>
            <Link to="/multiplayer" className="btn-primary inline-flex items-center space-x-2">
              <Play className="w-5 h-5" />
              <span>Join Multiplayer</span>
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="mt-16">
          <h2 className="text-3xl font-bold text-chess-dark mb-8">Features</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Concurrent Engine</h3>
              <p className="text-gray-600">Multi-threaded chess engine for fast AI moves</p>
            </div>
            <div className="text-center">
              <div className="bg-orange-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🌐</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Real-time Multiplayer</h3>
              <p className="text-gray-600">WebSocket-based live multiplayer matches</p>
            </div>
            <div className="text-center">
              <div className="bg-teal-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🎯</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Modern UI</h3>
              <p className="text-gray-600">Beautiful, responsive chess interface</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 