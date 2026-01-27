import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, Bot, Wrench, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { ProtocolEvent } from '../../types/ucp'

interface AgentThinkingProps {
  events: ProtocolEvent[]
  isLoading: boolean
}

interface ToolCall {
  id: string
  name: string
  args: Record<string, unknown>
  timestamp: string
  result?: {
    success: boolean
    data: Record<string, unknown>
  }
}

// Tool descriptions for user-friendly display
const TOOL_DESCRIPTIONS: Record<string, string> = {
  show_menu: 'Fetching product catalog',
  add_to_cart: 'Adding item to cart',
  view_cart: 'Loading cart contents',
  select_shipping: 'Setting delivery option',
  apply_discount: 'Applying discount code',
  complete_checkout: 'Processing order',
}

function ToolCallItem({ toolCall, isLast }: { toolCall: ToolCall; isLast: boolean }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const hasResult = !!toolCall.result
  const isSuccess = toolCall.result?.success !== false

  return (
    <div className={`relative ${!isLast ? 'pb-3' : ''}`}>
      {/* Vertical connector line */}
      {!isLast && (
        <div className="absolute left-[11px] top-6 bottom-0 w-0.5 bg-gray-200" />
      )}

      <div className="flex items-start gap-2">
        {/* Status icon */}
        <div className="relative z-10 mt-0.5">
          {!hasResult ? (
            <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
          ) : isSuccess ? (
            <CheckCircle className="w-6 h-6 text-green-500" />
          ) : (
            <XCircle className="w-6 h-6 text-red-500" />
          )}
        </div>

        {/* Tool call content */}
        <div className="flex-1 min-w-0">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-left w-full group"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
            )}
            <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 truncate">
              {TOOL_DESCRIPTIONS[toolCall.name] || toolCall.name}
            </span>
            <span className="text-xs text-gray-400 flex-shrink-0">
              {new Date(toolCall.timestamp).toLocaleTimeString()}
            </span>
          </button>

          {/* Expanded details */}
          {isExpanded && (
            <div className="mt-2 ml-5 space-y-2">
              {/* Tool name and arguments */}
              <div className="bg-gray-800 rounded-lg p-2 text-xs font-mono">
                <div className="text-gray-400 mb-1">
                  <Wrench className="w-3 h-3 inline mr-1" />
                  {toolCall.name}({Object.keys(toolCall.args).join(', ')})
                </div>
                <pre className="text-gray-100 whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(toolCall.args, null, 2)}
                </pre>
              </div>

              {/* Result if available */}
              {toolCall.result && (
                <div className={`rounded-lg p-2 text-xs font-mono ${
                  isSuccess ? 'bg-green-900' : 'bg-red-900'
                }`}>
                  <div className={`mb-1 ${isSuccess ? 'text-green-400' : 'text-red-400'}`}>
                    {isSuccess ? '✓ Success' : '✗ Failed'}
                  </div>
                  <pre className="text-gray-100 whitespace-pre-wrap overflow-x-auto max-h-32 overflow-y-auto">
                    {JSON.stringify(toolCall.result.data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function AgentThinking({ events, isLoading }: AgentThinkingProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([])

  // Process events to extract tool calls
  useEffect(() => {
    const calls: Record<string, ToolCall> = {}

    // Filter and process agent events
    const agentEvents = events.filter(
      (e) => e.type === 'agent_tool_call' || e.type === 'agent_tool_result'
    )

    for (const event of agentEvents) {
      if (event.type === 'agent_tool_call' && event.body_preview) {
        try {
          const body = JSON.parse(event.body_preview)
          calls[event.id] = {
            id: event.id,
            name: body.tool || 'unknown',
            args: body.args || {},
            timestamp: event.timestamp,
          }
        } catch {
          // Skip malformed events
        }
      } else if (event.type === 'agent_tool_result' && event.body_preview) {
        // Match result to call (result ID is `{call_id}_result`)
        const callId = event.id.replace('_result', '')
        if (calls[callId]) {
          try {
            const body = JSON.parse(event.body_preview)
            calls[callId].result = {
              success: body.success !== false,
              data: body.result || {},
            }
          } catch {
            // Skip malformed events
          }
        }
      }
    }

    setToolCalls(Object.values(calls))
  }, [events])

  // Auto-collapse after loading is done
  useEffect(() => {
    if (!isLoading && toolCalls.length > 0) {
      // Keep expanded for a moment so user can see final state
      const timer = setTimeout(() => {
        setIsCollapsed(true)
      }, 1500)
      return () => clearTimeout(timer)
    }
  }, [isLoading, toolCalls.length])

  // Don't show if no tool calls and not loading
  if (toolCalls.length === 0 && !isLoading) {
    return null
  }

  return (
    <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-100 overflow-hidden mb-4">
      {/* Header */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full px-4 py-2 flex items-center justify-between hover:bg-purple-100/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Bot className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="text-sm font-medium text-purple-900">
            Agent Reasoning
          </span>
          {isLoading && (
            <Loader2 className="w-4 h-4 text-purple-500 animate-spin" />
          )}
          {!isLoading && toolCalls.length > 0 && (
            <span className="text-xs text-purple-600 bg-purple-100 px-2 py-0.5 rounded-full">
              {toolCalls.length} tool{toolCalls.length !== 1 ? 's' : ''} called
            </span>
          )}
        </div>
        {isCollapsed ? (
          <ChevronRight className="w-4 h-4 text-purple-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-purple-400" />
        )}
      </button>

      {/* Content */}
      {!isCollapsed && (
        <div className="px-4 pb-3 pt-1">
          {toolCalls.length === 0 && isLoading ? (
            <div className="flex items-center gap-2 text-sm text-purple-600 py-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing your request...</span>
            </div>
          ) : (
            <div className="space-y-1">
              {toolCalls.map((toolCall, index) => (
                <ToolCallItem
                  key={toolCall.id}
                  toolCall={toolCall}
                  isLast={index === toolCalls.length - 1}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
