import { useState, useEffect, useCallback, useRef } from 'react'
import { ProtocolEvent } from '../types/ucp'

interface UseWebSocketReturn {
  events: ProtocolEvent[]
  isConnected: boolean
  clearEvents: () => void
  sendMessage: (message: string) => void
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [events, setEvents] = useState<ProtocolEvent[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'event' && data.data) {
            // Deduplicate by event ID to prevent double-display
            // (events can arrive both as "recent" on connect and as broadcasts)
            setEvents((prev) => {
              const newEvent = data.data as ProtocolEvent
              if (prev.some(e => e.id === newEvent.id)) {
                return prev // Already have this event
              }
              return [...prev, newEvent]
            })
          } else if (data.type === 'events_list' && data.data) {
            setEvents(data.data as ProtocolEvent[])
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        console.log('WebSocket disconnected')
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, 3000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (err) {
      console.error('Failed to connect WebSocket:', err)
      // Retry connection
      reconnectTimeoutRef.current = setTimeout(() => {
        connect()
      }, 3000)
    }
  }, [url])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  const clearEvents = useCallback(() => {
    setEvents([])
  }, [])

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(message)
    }
  }, [])

  return {
    events,
    isConnected,
    clearEvents,
    sendMessage,
  }
}
