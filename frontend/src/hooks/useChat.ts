import { useState, useCallback, useRef, useEffect } from 'react'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  toolCalls?: ToolCall[]
}

export interface ToolCall {
  name: string
  args: Record<string, unknown>
  status: 'started' | 'completed'
  result?: string
}

interface WSMessage {
  type: 'content' | 'tool_call' | 'done' | 'error' | 'pong'
  content?: string
  name?: string
  args?: Record<string, unknown>
  status?: string
  result?: string
  full_content?: string
  message?: string
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const currentMessageRef = useRef<Message | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const pingIntervalRef = useRef<number | null>(null)
  const reconnectCountRef = useRef(0)

  const startPing = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
    }
    pingIntervalRef.current = window.setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }, [])

  const stopPing = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
  }, [])

  const connect = useCallback(() => {
    // Don't connect if already connected or connecting
    const currentState = wsRef.current?.readyState
    console.log('[WebSocket] connect called, current state:', currentState)

    if (currentState === WebSocket.OPEN || currentState === WebSocket.CONNECTING) {
      console.log('[WebSocket] Already connected or connecting, skipping')
      return
    }

    // Close any existing connection first
    if (wsRef.current) {
      wsRef.current.onclose = null  // Prevent onclose handler
      wsRef.current.close()
      wsRef.current = null
    }

    setConnectionError(null)

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`
    console.log('[WebSocket] Connecting to:', wsUrl)

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws  // Set ref immediately

      ws.onopen = () => {
        console.log('[WebSocket] Connected!')
        // Only update state if this is still the current WebSocket
        if (wsRef.current === ws) {
          setIsConnected(true)
          setConnectionError(null)
          reconnectCountRef.current = 0
          startPing()
        }
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = null
        }
      }

      ws.onclose = (event) => {
        console.log('[WebSocket] Closed, wasClean:', event.wasClean, 'code:', event.code)
        // Only update state if this is still the current WebSocket
        if (wsRef.current === ws) {
          setIsConnected(false)
          wsRef.current = null
          stopPing()

        if (!event.wasClean && reconnectCountRef.current < 3) {
          const delay = Math.min(3000 * Math.pow(2, reconnectCountRef.current), 30000)
          setConnectionError(`Connection lost. Reconnecting in ${delay / 1000}s...`)
          reconnectCountRef.current += 1
          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect()
          }, delay)
        } else if (reconnectCountRef.current >= 3) {
          setConnectionError('Unable to connect to server. Please check if the backend is running.')
        }
        }  // end of if (wsRef.current === ws)
      }

      ws.onerror = () => {
        // Error will trigger onclose, so just log here
      }

      ws.onmessage = (event) => {
        const data: WSMessage = JSON.parse(event.data)

        if (data.type === 'pong') {
          return
        }

        switch (data.type) {
          case 'content':
            // Create assistant message if none exists
            if (!currentMessageRef.current) {
              const assistantMessage: Message = {
                id: `assistant-${Date.now()}`,
                role: 'assistant',
                content: data.content || '',
                toolCalls: [],
              }
              currentMessageRef.current = assistantMessage
              setMessages((prev) => [...prev, assistantMessage])
            } else {
              currentMessageRef.current.content += data.content || ''
              setMessages((prev) => {
                const updated = [...prev]
                const idx = updated.findIndex((m) => m.id === currentMessageRef.current?.id)
                if (idx !== -1) {
                  updated[idx] = { ...currentMessageRef.current! }
                }
                return updated
              })
            }
            break

          case 'tool_call':
            if (currentMessageRef.current) {
              const toolCall: ToolCall = {
                name: data.name || '',
                args: data.args || {},
                status: data.status as 'started' | 'completed',
                result: data.result,
              }

              if (data.status === 'started') {
                currentMessageRef.current.toolCalls = [
                  ...(currentMessageRef.current.toolCalls || []),
                  toolCall,
                ]
              } else {
                const calls = currentMessageRef.current.toolCalls || []
                const idx = calls.findIndex((tc) => tc.name === data.name && tc.status === 'started')
                if (idx !== -1) {
                  calls[idx] = toolCall
                }
                currentMessageRef.current.toolCalls = calls
              }

              setMessages((prev) => {
                const updated = [...prev]
                const idx = updated.findIndex((m) => m.id === currentMessageRef.current?.id)
                if (idx !== -1) {
                  updated[idx] = { ...currentMessageRef.current! }
                }
                return updated
              })
            }
            break

          case 'done':
            if (currentMessageRef.current) {
              currentMessageRef.current.content = data.full_content || currentMessageRef.current.content
              setMessages((prev) => {
                const updated = [...prev]
                const idx = updated.findIndex((m) => m.id === currentMessageRef.current?.id)
                if (idx !== -1) {
                  updated[idx] = { ...currentMessageRef.current! }
                }
                return updated
              })
            }
            currentMessageRef.current = null
            setIsLoading(false)
            break

          case 'error':
            if (currentMessageRef.current) {
              currentMessageRef.current.content = `Error: ${data.message}`
              setMessages((prev) => {
                const updated = [...prev]
                const idx = updated.findIndex((m) => m.id === currentMessageRef.current?.id)
                if (idx !== -1) {
                  updated[idx] = { ...currentMessageRef.current! }
                }
                return updated
              })
            }
            currentMessageRef.current = null
            setIsLoading(false)
            break
        }
      }

      console.log('[WebSocket] WebSocket object created, readyState:', ws.readyState)
    } catch (err) {
      console.error('[WebSocket] Failed to create:', err)
      setConnectionError('Failed to create WebSocket connection.')
    }
  }, [startPing, stopPing])

  const disconnect = useCallback(() => {
    console.log('[WebSocket] disconnect called')
    stopPing()
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.onclose = null  // Prevent onclose handler from firing
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [stopPing])

  const reconnect = useCallback(() => {
    disconnect()
    reconnectCountRef.current = 0
    setTimeout(() => connect(), 100)
  }, [connect, disconnect])

  const sendMessage = useCallback((content: string) => {
    const ws = wsRef.current
    console.log('[WebSocket] sendMessage called, ws:', !!ws, 'readyState:', ws?.readyState)

    if (!ws || ws.readyState !== WebSocket.OPEN) {
      // Try to reconnect automatically
      if (!ws || ws.readyState === WebSocket.CLOSED) {
        setConnectionError('Connection closed. Reconnecting...')
        reconnectCountRef.current = 0
        connect()
      } else {
        setConnectionError('Connection not ready. Please wait and try again.')
      }
      return
    }

    // Clear any previous error
    setConnectionError(null)

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
    }
    setMessages((prev) => [...prev, userMessage])

    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      toolCalls: [],
    }
    currentMessageRef.current = assistantMessage
    setMessages((prev) => [...prev, assistantMessage])
    setIsLoading(true)

    ws.send(JSON.stringify({ type: 'message', content }))
  }, [connect])

  const clearHistory = useCallback(async () => {
    try {
      await fetch('/api/history', { method: 'DELETE' })
      setMessages([])
      currentMessageRef.current = null
      setIsLoading(false)
      // Reconnect to trigger welcome message
      disconnect()
      setTimeout(() => connect(), 200)
    } catch (error) {
      setConnectionError('Failed to clear history. Server may be unavailable.')
    }
  }, [connect, disconnect])

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect()
    return () => disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return {
    messages,
    isConnected,
    isLoading,
    connectionError,
    sendMessage,
    clearHistory,
    reconnect,
  }
}
