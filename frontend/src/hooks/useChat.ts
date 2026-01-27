import { useState, useCallback } from 'react'
import { ChatMessage, CheckoutSession, ProductDisplay } from '../types/ucp'

interface ChatResponse {
  response: string
  checkout_session?: CheckoutSession
  products?: ProductDisplay[]
  show_products?: boolean
}

// Helper to check if checkout has changed meaningfully
function hasCheckoutChanged(prev?: CheckoutSession, next?: CheckoutSession): boolean {
  if (!prev && !next) return false
  if (!prev || !next) return true
  return prev.id !== next.id ||
         prev.status !== next.status ||
         prev.line_items.length !== next.line_items.length ||
         prev.totals?.total !== next.totals?.total
}

interface UseChatReturn {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
  sendMessage: (content: string) => Promise<void>
  clearMessages: () => void
  resetSession: () => Promise<void>
}

export function useChat(
  onCheckoutUpdate?: (session: CheckoutSession) => void
): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Welcome to **Cymbal Coffee Shop**! ☕

**How to order:**

1. **Browse** - Say "show menu" to see products
2. **Add items** - Click "Add" or say "add a latte"
3. **Select delivery** - Choose pickup or delivery
4. **Apply discount** - Try code "DEMO20" for 20% off
5. **Checkout** - Complete your order

What would you like today?`,
      timestamp: new Date().toISOString(),
    },
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(
    async (content: string) => {
      // Add user message
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMessage])
      setIsLoading(true)
      setError(null)

      try {
        const response = await fetch('http://localhost:8000/api/v1/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: content }),
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data: ChatResponse = await response.json()

        // Add assistant message with checkout if present
        const assistantMessage: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString(),
          products: data.products,
          show_products: data.show_products,
          checkout: data.checkout_session,
        }
        setMessages((prev) => [...prev, assistantMessage])

        // Update checkout session if present
        if (data.checkout_session && onCheckoutUpdate) {
          onCheckoutUpdate(data.checkout_session)
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to send message'
        setError(errorMessage)

        // Add error message from assistant
        const errorAssistantMessage: ChatMessage = {
          id: `assistant-error-${Date.now()}`,
          role: 'assistant',
          content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, errorAssistantMessage])
      } finally {
        setIsLoading(false)
      }
    },
    [onCheckoutUpdate]
  )

  const clearMessages = useCallback(() => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `Welcome to **Cymbal Coffee Shop**! ☕

**How to order:**

1. **Browse** - Say "show menu" to see products
2. **Add items** - Click "Add" or say "add a latte"
3. **Select delivery** - Choose pickup or delivery
4. **Apply discount** - Try code "DEMO20" for 20% off
5. **Checkout** - Complete your order

What would you like today?`,
        timestamp: new Date().toISOString(),
      },
    ])
    setError(null)
  }, [])

  const resetSession = useCallback(async () => {
    try {
      await fetch('http://localhost:8000/api/v1/chat/reset', {
        method: 'POST',
      })
      clearMessages()
    } catch (err) {
      console.error('Failed to reset session:', err)
    }
  }, [clearMessages])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    resetSession,
  }
}
