import { useChat } from '../hooks/useChat'
import { MessageList } from './MessageList'
import { InputArea } from './InputArea'

export function ChatContainer() {
  const { messages, isConnected, isLoading, connectionError, sendMessage, clearHistory, reconnect } = useChat()

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-gray-800">TestAIAgent: Chat with Everlasting Cabinetory LLC</h1>
          <span
            className={`px-2 py-0.5 text-xs rounded-full ${
              isConnected
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <button
          onClick={clearHistory}
          className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
        >
          Clear History
        </button>
      </header>

      {/* Connection Error Banner */}
      {connectionError && (
        <div className="px-4 py-3 bg-red-50 border-b border-red-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="text-sm text-red-700">{connectionError}</span>
          </div>
          <button
            onClick={reconnect}
            className="px-3 py-1.5 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            Reconnect
          </button>
        </div>
      )}

      {/* Messages */}
      <MessageList messages={messages} />

      {/* Input */}
      <InputArea onSend={sendMessage} disabled={!isConnected || isLoading} />
    </div>
  )
}
