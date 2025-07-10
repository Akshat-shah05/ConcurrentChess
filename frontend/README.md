# Concurrent Chess Frontend

A modern React-based chess frontend with AI and multiplayer support.

## Features

- **AI Mode**: Play against the chess engine with configurable difficulty levels
- **Multiplayer Mode**: Real-time multiplayer games using WebSocket connections
- **Modern UI**: Beautiful, responsive interface with Tailwind CSS
- **TypeScript**: Full type safety for better development experience

## Prerequisites

- Node.js 16+ and npm
- Backend server running on `localhost:8000`
- WebSocket server running on `localhost:8766`

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to `http://localhost:3000`

## Development

- **Build**: `npm run build`
- **Preview**: `npm run preview`
- **Lint**: `npm run lint`

## Architecture

### Components
- `ChessBoard`: Main chess board with piece rendering and move handling
- `ChessPiece`: Individual chess piece component
- `Layout`: Navigation and layout wrapper

### Pages
- `Home`: Landing page with mode selection
- `AIGame`: AI gameplay using REST API
- `MultiplayerGame`: Multiplayer gameplay using WebSocket

### Services
- `api.ts`: REST API client for AI mode
- `websocket.ts`: WebSocket client for multiplayer mode

### Types
- `chess.ts`: TypeScript interfaces for chess game state

## Backend Integration

The frontend expects the backend to be running with:
- REST API on `http://localhost:8000`
- WebSocket server on `ws://localhost:8766`

Make sure to start the backend server before running the frontend. 