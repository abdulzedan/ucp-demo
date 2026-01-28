import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Chat from './components/Chat/Chat'
import Visualizer from './components/Visualizer/Visualizer'
import FlowDiagram from './components/FlowDiagram/FlowDiagram'
import Inspector from './components/Inspector/Inspector'
import { ProtocolEvent, CheckoutSession } from './types/ucp'
import { useWebSocket } from './hooks/useWebSocket'

const queryClient = new QueryClient()

type Tab = 'visualizer' | 'flow' | 'inspector'

function AppContent() {
  const [activeTab, setActiveTab] = useState<Tab>('visualizer')
  const [selectedEvent, setSelectedEvent] = useState<ProtocolEvent | null>(null)
  const [checkoutSession, setCheckoutSession] = useState<CheckoutSession | null>(null)

  const { events, isConnected, clearEvents } = useWebSocket('ws://localhost:8000/ws/events')

  const handleEventSelect = (event: ProtocolEvent) => {
    setSelectedEvent(event)
    setActiveTab('inspector')
  }

  const handleCheckoutUpdate = (session: CheckoutSession) => {
    setCheckoutSession(session)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">U</span>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">UCP Demo</h1>
              <p className="text-sm text-gray-500">Interactive Universal Commerce Protocol Explorer</p>
            </div>
            <div className="hidden md:flex items-center gap-2 ml-4 pl-4 border-l border-gray-200">
              <a
                href="https://ucp.dev"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-purple-600 hover:text-purple-800 hover:underline"
              >
                ucp.dev
              </a>
              <span className="text-gray-300">|</span>
              <a
                href="https://github.com/Universal-Commerce-Protocol/samples"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-500 hover:text-gray-700 hover:underline"
              >
                GitHub
              </a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <button
              onClick={clearEvents}
              className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              Clear Events
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-73px)]">
        {/* Left Panel - Chat */}
        <div className="w-1/2 border-r border-gray-200 bg-white">
          <Chat onCheckoutUpdate={handleCheckoutUpdate} events={events} />
        </div>

        {/* Right Panel - Visualizer/Inspector */}
        <div className="w-1/2 flex flex-col bg-gray-50">
          {/* Tab Navigation */}
          <div className="flex border-b border-gray-200 bg-white">
            <button
              onClick={() => setActiveTab('visualizer')}
              className={`px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'visualizer'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Protocol Events
            </button>
            <button
              onClick={() => setActiveTab('flow')}
              className={`px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'flow'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Checkout Flow
            </button>
            <button
              onClick={() => setActiveTab('inspector')}
              className={`px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'inspector'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Inspector
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'visualizer' && (
              <Visualizer
                events={events}
                onEventSelect={handleEventSelect}
              />
            )}
            {activeTab === 'flow' && (
              <FlowDiagram
                checkoutSession={checkoutSession}
              />
            )}
            {activeTab === 'inspector' && (
              <Inspector
                event={selectedEvent}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}

export default App
