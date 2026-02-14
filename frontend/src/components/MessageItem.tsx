import ReactMarkdown from 'react-markdown'
import { Message } from '../hooks/useChat'
import { ToolCallCard } from './ToolCallCard'

interface MessageItemProps {
  message: Message
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-800'
        }`}
      >
        {/* Tool calls */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mb-2">
            {message.toolCalls.map((tc, idx) => (
              <ToolCallCard key={`${tc.name}-${idx}`} toolCall={tc} />
            ))}
          </div>
        )}

        {/* Message content */}
        {message.content && (
          <div className={`markdown-content ${isUser ? 'text-white' : ''}`}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {/* Loading indicator */}
        {!message.content && message.role === 'assistant' && (
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        )}
      </div>
    </div>
  )
}
