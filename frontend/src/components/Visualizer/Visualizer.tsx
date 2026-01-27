import { ArrowUpRight, ArrowDownLeft, Clock, CheckCircle, XCircle, AlertCircle, BookOpen, ExternalLink } from 'lucide-react'
import { ProtocolEvent } from '../../types/ucp'

interface VisualizerProps {
  events: ProtocolEvent[]
  onEventSelect?: (event: ProtocolEvent) => void
}

// UCP concept badge colors
const conceptColors: Record<string, string> = {
  'UCP Profile': 'bg-indigo-100 text-indigo-700',
  'Checkout Capability': 'bg-blue-100 text-blue-700',
  'Checkout Session': 'bg-cyan-100 text-cyan-700',
  'Checkout Lifecycle': 'bg-teal-100 text-teal-700',
  'Payment & Order': 'bg-green-100 text-green-700',
  'Payment Handler': 'bg-emerald-100 text-emerald-700',
  'Error Handling': 'bg-red-100 text-red-700',
}

function getMethodColor(method: string): string {
  switch (method.toUpperCase()) {
    case 'GET':
      return 'bg-green-100 text-green-700'
    case 'POST':
      return 'bg-blue-100 text-blue-700'
    case 'PUT':
      return 'bg-yellow-100 text-yellow-700'
    case 'DELETE':
      return 'bg-red-100 text-red-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

function getStatusIcon(statusCode?: number) {
  if (!statusCode) return null
  if (statusCode >= 200 && statusCode < 300) {
    return <CheckCircle className="w-4 h-4 text-green-500" />
  }
  if (statusCode >= 400 && statusCode < 500) {
    return <AlertCircle className="w-4 h-4 text-yellow-500" />
  }
  if (statusCode >= 500) {
    return <XCircle className="w-4 h-4 text-red-500" />
  }
  return null
}

function EventCard({ event, onClick }: { event: ProtocolEvent; onClick?: () => void }) {
  const isRequest = event.direction === 'request'
  const timestamp = new Date(event.timestamp).toLocaleTimeString()
  const conceptColor = event.ucp_concept ? conceptColors[event.ucp_concept] || 'bg-gray-100 text-gray-700' : ''

  return (
    <div
      onClick={onClick}
      className={`p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
        isRequest
          ? 'bg-blue-50 border-blue-200 hover:border-blue-300'
          : 'bg-green-50 border-green-200 hover:border-green-300'
      }`}
    >
      {/* Header with title and status */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isRequest ? (
            <ArrowUpRight className="w-4 h-4 text-blue-500" />
          ) : (
            <ArrowDownLeft className="w-4 h-4 text-green-500" />
          )}
          <span className="font-medium text-gray-900 text-sm">
            {event.title || event.type}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {event.status_code && (
            <div className="flex items-center gap-1">
              {getStatusIcon(event.status_code)}
              <span>{event.status_code}</span>
            </div>
          )}
          {event.duration_ms && (
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{event.duration_ms}ms</span>
            </div>
          )}
        </div>
      </div>

      {/* Method and path */}
      <div className="flex items-center gap-2 mb-2">
        <span className={`px-2 py-0.5 text-xs font-medium rounded ${getMethodColor(event.method)}`}>
          {event.method}
        </span>
        <span className="font-mono text-xs text-gray-600 truncate">{event.path}</span>
      </div>

      {/* Educational description */}
      {event.description && (
        <p className="text-xs text-gray-600 mb-2 leading-relaxed">
          {event.description}
        </p>
      )}

      {/* Tags: UCP concept and learn more */}
      <div className="flex items-center gap-2 flex-wrap">
        {event.has_ucp && (
          <span className="px-2 py-0.5 text-xs font-medium rounded bg-purple-100 text-purple-700">
            UCP Protocol
          </span>
        )}
        {event.ucp_concept && (
          <span className={`px-2 py-0.5 text-xs font-medium rounded ${conceptColor}`}>
            {event.ucp_concept}
          </span>
        )}
        {event.learn_more && (
          <a
            href={event.learn_more}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 px-2 py-0.5 text-xs text-blue-600 hover:text-blue-800 hover:underline"
          >
            <BookOpen className="w-3 h-3" />
            Learn more
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      <div className="mt-2 text-xs text-gray-400">{timestamp}</div>
    </div>
  )
}

export default function Visualizer({ events, onEventSelect }: VisualizerProps) {
  if (events.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            <ArrowUpRight className="w-8 h-8 text-gray-400" />
          </div>
          <p className="font-medium">No protocol events yet</p>
          <p className="text-sm mt-1">Start a conversation to see UCP messages</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="space-y-3">
        {events.map((event) => (
          <EventCard
            key={event.id}
            event={event}
            onClick={() => onEventSelect?.(event)}
          />
        ))}
      </div>
    </div>
  )
}
