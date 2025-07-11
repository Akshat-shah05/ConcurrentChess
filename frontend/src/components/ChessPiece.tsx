import type { ChessPiece as ChessPieceType } from '@/types/chess'

interface ChessPieceProps {
  piece: ChessPieceType
}

export function ChessPiece({ piece }: ChessPieceProps) {
  const getPieceImage = (kind: string, color: string) => {
    const pieceCode = `${color === 'white' ? 'w' : 'b'}${kind}`
    return `/${pieceCode}.png`
  }

  const getPieceSymbol = (kind: string, color: string) => {
    const symbols = {
      'P': color === 'white' ? '♙' : '♟',
      'N': color === 'white' ? '♘' : '♞',
      'B': color === 'white' ? '♗' : '♝',
      'R': color === 'white' ? '♖' : '♜',
      'Q': color === 'white' ? '♕' : '♛',
      'K': color === 'white' ? '♔' : '♚',
    }
    return symbols[kind as keyof typeof symbols] || '?'
  }

  const imageSrc = getPieceImage(piece.kind, piece.color)
  const symbol = getPieceSymbol(piece.kind, piece.color)

  return (
    <div className="chess-piece">
      <img 
        src={imageSrc} 
        alt={`${piece.color} ${piece.kind}`}
        className="w-full h-full object-contain"
        onError={(e) => {
          console.log('Image failed to load:', imageSrc)
          // Fallback to Unicode symbol if image fails to load
          const target = e.target as HTMLImageElement
          target.style.display = 'none'
          const fallback = target.nextElementSibling as HTMLElement
          if (fallback) {
            fallback.style.display = 'block'
          }
        }}
      />
      <span 
        className={`text-2xl md:text-3xl lg:text-4xl drop-shadow-lg ${piece.color === 'white' ? 'text-white' : 'text-black'}`}
        style={{ display: 'none' }}
      >
        {symbol}
      </span>
    </div>
  )
} 