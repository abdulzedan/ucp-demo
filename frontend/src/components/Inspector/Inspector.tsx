import { useState } from 'react'
import { Copy, Check, ArrowUpRight, ArrowDownLeft, Code } from 'lucide-react'
import { ProtocolEvent } from '../../types/ucp'

interface InspectorProps {
  event: ProtocolEvent | null
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
      title="Copy to clipboard"
    >
      {copied ? (
        <Check className="w-4 h-4 text-green-500" />
      ) : (
        <Copy className="w-4 h-4" />
      )}
    </button>
  )
}

function JsonViewer({ data, title }: { data: string; title: string }) {
  let formattedJson: string
  let jsonObject: unknown

  try {
    jsonObject = JSON.parse(data)
    formattedJson = JSON.stringify(jsonObject, null, 2)
  } catch {
    formattedJson = data
    jsonObject = null
  }

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800">
        <span className="text-sm font-medium text-gray-300">{title}</span>
        <CopyButton text={formattedJson} />
      </div>
      <div className="max-h-96 overflow-y-auto">
        <pre className="p-4 text-sm whitespace-pre-wrap break-words">
          <code className="text-gray-100">{formattedJson}</code>
        </pre>
      </div>
    </div>
  )
}

function MetadataRow({ label, value }: { label: string; value: string | number | undefined }) {
  if (value === undefined) return null

  return (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900">{value}</span>
    </div>
  )
}

export default function Inspector({ event }: InspectorProps) {
  if (!event) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            <Code className="w-8 h-8 text-gray-400" />
          </div>
          <p className="font-medium">No event selected</p>
          <p className="text-sm mt-1">Click on a protocol event to inspect it</p>
        </div>
      </div>
    )
  }

  const isRequest = event.direction === 'request'

  return (
    <div className="h-full overflow-y-auto p-4">
      {/* Event Header */}
      <div className={`rounded-lg p-4 mb-4 ${
        isRequest ? 'bg-blue-50 border border-blue-200' : 'bg-green-50 border border-green-200'
      }`}>
        <div className="flex items-center gap-2 mb-2">
          {isRequest ? (
            <ArrowUpRight className="w-5 h-5 text-blue-500" />
          ) : (
            <ArrowDownLeft className="w-5 h-5 text-green-500" />
          )}
          <span className="font-medium text-gray-900">
            {isRequest ? 'Request' : 'Response'}
          </span>
          {event.has_ucp && (
            <span className="px-2 py-0.5 text-xs font-medium rounded bg-purple-100 text-purple-700">
              UCP Protocol
            </span>
          )}
        </div>
        <div className="font-mono text-lg text-gray-900">
          <span className={`font-bold ${
            event.method === 'GET' ? 'text-green-600' :
            event.method === 'POST' ? 'text-blue-600' :
            event.method === 'PUT' ? 'text-yellow-600' :
            event.method === 'DELETE' ? 'text-red-600' :
            'text-gray-600'
          }`}>
            {event.method}
          </span>
          {' '}
          {event.path}
        </div>
      </div>

      {/* Metadata */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <h3 className="font-medium text-gray-900 mb-2">Metadata</h3>
        <MetadataRow label="Event ID" value={event.id} />
        <MetadataRow label="Type" value={event.type} />
        <MetadataRow label="Timestamp" value={new Date(event.timestamp).toLocaleString()} />
        <MetadataRow label="Status Code" value={event.status_code} />
        <MetadataRow label="Duration" value={event.duration_ms ? `${event.duration_ms}ms` : undefined} />
      </div>

      {/* Body Preview */}
      {event.body_preview && (
        <div className="mb-4">
          <h3 className="font-medium text-gray-900 mb-2">Body</h3>
          <JsonViewer data={event.body_preview} title="JSON Payload" />
        </div>
      )}

      {/* UCP Educational Info */}
      {event.has_ucp && (
        <div className="bg-purple-50 rounded-lg border border-purple-200 p-4">
          <h3 className="font-medium text-purple-900 mb-2 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-purple-200 flex items-center justify-center text-xs font-bold text-purple-700">
              U
            </span>
            UCP Protocol Details
          </h3>

          {/* Event-specific explanation */}
          {event.title && (
            <div className="mb-3">
              <h4 className="text-sm font-semibold text-purple-800">{event.title}</h4>
              {event.description && (
                <p className="text-sm text-purple-700 mt-1">{event.description}</p>
              )}
            </div>
          )}

          {/* Detailed commentary - markdown-like rendering */}
          {event.details && (
            <div className="mb-3 bg-white rounded-lg border border-purple-100 p-3">
              <h5 className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-2">
                Detailed Explanation
              </h5>
              <div className="text-sm text-gray-700 space-y-2 whitespace-pre-wrap">
                {event.details.split('\n\n').map((paragraph, idx) => (
                  <div key={idx} className="leading-relaxed">
                    {paragraph.split('\n').map((line, lineIdx) => {
                      // Handle bold text with **
                      const parts = line.split(/(\*\*[^*]+\*\*)/g)
                      return (
                        <p key={lineIdx} className={line.startsWith('```') ? 'font-mono text-xs bg-gray-100 rounded px-2 py-1 my-1' : ''}>
                          {parts.map((part, partIdx) => {
                            if (part.startsWith('**') && part.endsWith('**')) {
                              return <strong key={partIdx} className="font-semibold text-purple-800">{part.slice(2, -2)}</strong>
                            }
                            // Handle bullet points
                            if (part.startsWith('• ')) {
                              return <span key={partIdx} className="block pl-2">{part}</span>
                            }
                            // Handle code blocks
                            if (part.startsWith('`') && part.endsWith('`') && !part.startsWith('```')) {
                              return <code key={partIdx} className="bg-gray-100 px-1 rounded text-xs font-mono">{part.slice(1, -1)}</code>
                            }
                            return part
                          })}
                        </p>
                      )
                    })}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* UCP Concept tag */}
          {event.ucp_concept && (
            <div className="mb-3">
              <span className="text-xs text-purple-600">Related UCP Concept:</span>
              <span className="ml-2 px-2 py-0.5 text-xs font-medium rounded bg-purple-200 text-purple-800">
                {event.ucp_concept}
              </span>
            </div>
          )}

          <div className="border-t border-purple-200 pt-3 mt-3">
            <div className="text-xs text-purple-600 space-y-1">
              <p><strong>Protocol Version:</strong> 2026-01-11</p>
              <p>
                <strong>Specification:</strong>{' '}
                <a
                  href="https://ucp.dev/specification/overview/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:text-purple-800"
                >
                  ucp.dev/specification
                </a>
              </p>
              {event.learn_more && (
                <p>
                  <strong>Learn more:</strong>{' '}
                  <a
                    href={event.learn_more}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline hover:text-purple-800"
                  >
                    {event.learn_more.replace('https://', '')}
                  </a>
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
