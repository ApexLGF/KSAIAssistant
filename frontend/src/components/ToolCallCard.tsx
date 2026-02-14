import { useState } from 'react'
import { ToolCall } from '../hooks/useChat'

interface ToolCallCardProps {
  toolCall: ToolCall
}

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false)

  const isCompleted = toolCall.status === 'completed'

  return (
    <div className="my-2 border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-gray-100"
      >
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isCompleted ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'}`} />
          <span className="font-mono text-sm font-medium text-gray-700">{toolCall.name}</span>
          <span className="text-xs text-gray-500">
            {isCompleted ? 'completed' : 'running...'}
          </span>
        </div>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="px-3 py-2 border-t border-gray-200 bg-white">
          <div className="mb-2">
            <span className="text-xs font-medium text-gray-500">Arguments:</span>
            <pre className="mt-1 p-2 bg-gray-800 text-gray-100 rounded text-xs overflow-x-auto">
              {JSON.stringify(toolCall.args, null, 2)}
            </pre>
          </div>
          {toolCall.result && (
            <div>
              <span className="text-xs font-medium text-gray-500">Result:</span>
              <pre className="mt-1 p-2 bg-gray-800 text-gray-100 rounded text-xs overflow-x-auto max-h-48">
                {toolCall.result.length > 500 ? toolCall.result.slice(0, 500) + '...' : toolCall.result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
