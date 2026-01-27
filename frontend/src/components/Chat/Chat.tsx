import { useState, useRef, useEffect } from 'react'
import { Send, RotateCcw, Bot, User, Plus } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useChat } from '../../hooks/useChat'
import { CheckoutSession, ChatMessage, ProductDisplay, ProtocolEvent } from '../../types/ucp'
import CheckoutCard from './CheckoutCard'
import AgentThinking from './AgentThinking'

interface ChatProps {
  onCheckoutUpdate?: (session: CheckoutSession) => void
  events?: ProtocolEvent[]
}

interface ProductCardProps {
  product: ProductDisplay
  onAddToCart: (productId: string) => void
}

function ProductCard({ product, onAddToCart }: ProductCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      {product.image_url && (
        <img
          src={product.image_url}
          alt={product.title}
          className="w-full h-32 object-cover"
        />
      )}
      <div className="p-3">
        <h4 className="font-medium text-gray-900 text-sm">{product.title}</h4>
        {product.description && (
          <p className="text-xs text-gray-500 mt-1">{product.description}</p>
        )}
        <div className="flex items-center justify-between mt-2">
          <span className="font-semibold text-blue-600">{product.price}</span>
          <button
            onClick={() => onAddToCart(product.id)}
            className="flex items-center gap-1 px-2 py-1 bg-blue-500 text-white text-xs rounded-full hover:bg-blue-600 transition-colors"
          >
            <Plus className="w-3 h-3" />
            Add
          </button>
        </div>
      </div>
    </div>
  )
}

interface MessageBubbleProps {
  message: ChatMessage
  onAddToCart?: (productId: string) => void
  onCompleteCheckout?: () => void
}

function MessageBubble({ message, onAddToCart, onCompleteCheckout }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? 'bg-blue-500' : 'bg-gradient-to-br from-purple-500 to-pink-500'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>
      <div className={`max-w-[85%] ${isUser ? '' : ''}`}>
        <div
          className={`rounded-2xl px-4 py-2 ${
            isUser
              ? 'bg-blue-500 text-white rounded-br-md'
              : 'bg-gray-100 text-gray-900 rounded-bl-md'
          }`}
        >
          <div className={`text-sm prose prose-sm max-w-none ${
            isUser ? 'prose-invert' : ''
          }`}>
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                ul: ({ children }) => <ul className="list-disc list-inside mb-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-1">{children}</ol>,
                li: ({ children }) => <li className="mb-0.5">{children}</li>,
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
          <p
            className={`text-xs mt-1 ${
              isUser ? 'text-blue-100' : 'text-gray-400'
            }`}
          >
            {new Date(message.timestamp).toLocaleTimeString()}
          </p>
        </div>

        {/* Product Grid */}
        {message.show_products && message.products && message.products.length > 0 && (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {message.products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={onAddToCart || (() => {})}
              />
            ))}
          </div>
        )}

        {/* Checkout Card */}
        {message.checkout && (
          <CheckoutCard
            checkout={message.checkout}
            onCompleteCheckout={
              message.checkout.status === 'ready_for_complete' ? onCompleteCheckout : undefined
            }
          />
        )}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-gradient-to-br from-purple-500 to-pink-500">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
        <div className="flex gap-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  )
}

export default function Chat({ onCheckoutUpdate, events = [] }: ChatProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, isLoading, sendMessage, resetSession } = useChat(onCheckoutUpdate)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const message = input.trim()
    setInput('')
    await sendMessage(message)
  }

  const handleQuickAction = async (action: string) => {
    if (isLoading) return
    await sendMessage(action)
  }

  const handleAddToCart = async (productId: string) => {
    if (isLoading) return
    await sendMessage(`Add ${productId} to my cart`)
  }

  const handleCompleteCheckout = async () => {
    if (isLoading) return
    await sendMessage('Complete my order')
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-gray-900">AI Shopping Assistant</h2>
          <p className="text-xs text-gray-500">Powered by UCP Protocol</p>
        </div>
        <button
          onClick={resetSession}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          title="Reset Session"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-2 border-b border-gray-100 flex gap-2 overflow-x-auto">
        <button
          onClick={() => handleQuickAction('What products do you have?')}
          className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-full whitespace-nowrap transition-colors"
        >
          Browse Products
        </button>
        <button
          onClick={() => handleQuickAction('Add a large latte to my cart')}
          className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-full whitespace-nowrap transition-colors"
        >
          Add Latte
        </button>
        <button
          onClick={() => handleQuickAction('Apply discount code DEMO20')}
          className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-full whitespace-nowrap transition-colors"
        >
          Apply Discount
        </button>
        <button
          onClick={() => handleQuickAction("What's in my cart?")}
          className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-full whitespace-nowrap transition-colors"
        >
          View Cart
        </button>
        <button
          onClick={() => handleQuickAction('Complete my order')}
          className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-full whitespace-nowrap transition-colors"
        >
          Checkout
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onAddToCart={handleAddToCart}
            onCompleteCheckout={handleCompleteCheckout}
          />
        ))}
        {/* Agent Thinking Panel - shows tool calls while processing */}
        <AgentThinking events={events} isLoading={isLoading} />
        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="px-4 py-3 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about shopping..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  )
}
