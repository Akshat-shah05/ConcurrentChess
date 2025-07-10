import { useEffect, useState } from 'react'
import { chessAPI } from '@/services/api'

interface EvaluationBarProps {
  gameId: string
  className?: string
}

export function EvaluationBar({ gameId, className = '' }: EvaluationBarProps) {
  const [evaluation, setEvaluation] = useState<number>(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchEvaluation = async () => {
    if (!gameId) return
    
    try {
      setLoading(true)
      setError(null)
      const response = await chessAPI.getEvaluation(gameId)
      setEvaluation(response.evaluation)
    } catch (err) {
      console.error('Failed to fetch evaluation:', err)
      setError('Failed to load evaluation')
    } finally {
      setLoading(false)
    }
  }

  // Fetch evaluation when gameId changes
  useEffect(() => {
    fetchEvaluation()
  }, [gameId])

  // Refresh evaluation every 2 seconds
  useEffect(() => {
    const interval = setInterval(fetchEvaluation, 2000)
    return () => clearInterval(interval)
  }, [gameId])

  const getEvaluationColor = (score: number) => {
    if (score > 1.0) return 'bg-green-500'
    if (score > 0.5) return 'bg-green-400'
    if (score > 0.1) return 'bg-green-300'
    if (score < -1.0) return 'bg-red-500'
    if (score < -0.5) return 'bg-red-400'
    if (score < -0.1) return 'bg-red-300'
    return 'bg-gray-400'
  }

  const getEvaluationText = (score: number) => {
    if (score > 0) return `+${score.toFixed(1)}`
    return score.toFixed(1)
  }

  const clampedEvaluation = Math.max(-5, Math.min(5, evaluation))
  const barHeight = 50 + (clampedEvaluation * 10) // 50% base + evaluation adjustment

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <div className="text-sm font-medium text-gray-700 mb-2">Evaluation</div>
      
      <div className="relative w-8 h-64 bg-gray-200 rounded-lg overflow-hidden border-2 border-gray-300">
        {/* Evaluation bar */}
        <div 
          className={`absolute bottom-0 left-0 right-0 transition-all duration-500 ${getEvaluationColor(evaluation)}`}
          style={{ 
            height: `${barHeight}%`,
            minHeight: '4px',
            maxHeight: '100%'
          }}
        />
        
        {/* Center line */}
        <div className="absolute top-1/2 left-0 right-0 h-px bg-gray-400 transform -translate-y-px" />
        
        {/* Evaluation text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="bg-white bg-opacity-90 px-2 py-1 rounded text-xs font-mono">
            {loading ? '...' : error ? 'ERR' : getEvaluationText(evaluation)}
          </div>
        </div>
      </div>
      
      {/* Labels */}
      <div className="mt-2 text-xs text-gray-600 space-y-1">
        <div>White</div>
        <div className="text-gray-400">Equal</div>
        <div>Black</div>
      </div>
    </div>
  )
} 