import { CheckoutSession, CheckoutStatus } from '../../types/ucp'
import { Check, Clock, AlertTriangle, XCircle, ShoppingCart, CreditCard } from 'lucide-react'

interface FlowDiagramProps {
  checkoutSession: CheckoutSession | null
}

interface StatusNodeProps {
  status: CheckoutStatus
  label: string
  isActive: boolean
  isPast: boolean
  icon: React.ReactNode
}

const STATUS_ORDER: CheckoutStatus[] = [
  'incomplete',
  'requires_escalation',
  'ready_for_complete',
  'complete_in_progress',
  'completed',
]

function StatusNode({ label, isActive, isPast, icon }: StatusNodeProps) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
          isActive
            ? 'bg-blue-500 text-white ring-4 ring-blue-200'
            : isPast
            ? 'bg-green-500 text-white'
            : 'bg-gray-200 text-gray-400'
        }`}
      >
        {isPast ? <Check className="w-6 h-6" /> : icon}
      </div>
      <span
        className={`mt-2 text-xs font-medium text-center ${
          isActive ? 'text-blue-600' : isPast ? 'text-green-600' : 'text-gray-400'
        }`}
      >
        {label}
      </span>
    </div>
  )
}

function Connector({ isActive }: { isActive: boolean }) {
  return (
    <div className="flex-1 flex items-center px-2">
      <div
        className={`h-1 w-full rounded transition-all ${
          isActive ? 'bg-green-500' : 'bg-gray-200'
        }`}
      />
    </div>
  )
}

function getStatusIndex(status: CheckoutStatus): number {
  return STATUS_ORDER.indexOf(status)
}

function getStatusLabel(status: CheckoutStatus): string {
  switch (status) {
    case 'incomplete':
      return 'Incomplete'
    case 'requires_escalation':
      return 'Needs Input'
    case 'ready_for_complete':
      return 'Ready'
    case 'complete_in_progress':
      return 'Processing'
    case 'completed':
      return 'Completed'
    case 'canceled':
      return 'Canceled'
    default:
      return status
  }
}

function getStatusIcon(status: CheckoutStatus): React.ReactNode {
  switch (status) {
    case 'incomplete':
      return <ShoppingCart className="w-5 h-5" />
    case 'requires_escalation':
      return <AlertTriangle className="w-5 h-5" />
    case 'ready_for_complete':
      return <CreditCard className="w-5 h-5" />
    case 'complete_in_progress':
      return <Clock className="w-5 h-5" />
    case 'completed':
      return <Check className="w-5 h-5" />
    case 'canceled':
      return <XCircle className="w-5 h-5" />
    default:
      return <Clock className="w-5 h-5" />
  }
}

function SessionDetails({ session }: { session: CheckoutSession }) {
  return (
    <div className="mt-6 bg-white rounded-lg border border-gray-200 p-4">
      <h4 className="font-medium text-gray-900 mb-3">Session Details</h4>

      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Session ID</span>
          <span className="font-mono text-gray-700">{session.id.slice(0, 8)}...</span>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Status</span>
          <span className={`font-medium ${
            session.status === 'completed' ? 'text-green-600' :
            session.status === 'canceled' ? 'text-red-600' :
            'text-blue-600'
          }`}>
            {getStatusLabel(session.status)}
          </span>
        </div>

        {session.line_items.length > 0 && (
          <div>
            <span className="text-sm text-gray-500">Items ({session.line_items.length})</span>
            <div className="mt-1 space-y-1">
              {session.line_items.map((item) => (
                <div key={item.id} className="flex justify-between text-sm">
                  <span className="text-gray-700">{item.quantity}x {item.title}</span>
                  <span className="font-medium">${(item.total_price / 100).toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {session.totals && (
          <div className="border-t border-gray-100 pt-2 mt-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Subtotal</span>
              <span>${(session.totals.subtotal / 100).toFixed(2)}</span>
            </div>
            {session.totals.discount > 0 && (
              <div className="flex justify-between text-sm text-green-600">
                <span>Discount</span>
                <span>-${(session.totals.discount / 100).toFixed(2)}</span>
              </div>
            )}
            {session.totals.shipping > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Shipping</span>
                <span>${(session.totals.shipping / 100).toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between text-sm font-medium mt-1">
              <span>Total</span>
              <span>${(session.totals.total / 100).toFixed(2)}</span>
            </div>
          </div>
        )}

        {session.order && (
          <div className="border-t border-gray-100 pt-2 mt-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Order ID</span>
              <span className="font-mono text-green-600">{session.order.id}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function FlowDiagram({ checkoutSession }: FlowDiagramProps) {
  if (!checkoutSession) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            <ShoppingCart className="w-8 h-8 text-gray-400" />
          </div>
          <p className="font-medium">No active checkout</p>
          <p className="text-sm mt-1">Add items to cart to see the checkout flow</p>
        </div>
      </div>
    )
  }

  const currentIndex = getStatusIndex(checkoutSession.status)
  const isCanceled = checkoutSession.status === 'canceled'

  if (isCanceled) {
    return (
      <div className="h-full p-6">
        <div className="flex items-center justify-center py-8">
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
            <span className="mt-3 text-lg font-medium text-red-600">Checkout Canceled</span>
          </div>
        </div>
        <SessionDetails session={checkoutSession} />
      </div>
    )
  }

  return (
    <div className="h-full p-6 overflow-y-auto">
      {/* Status Flow */}
      <div className="flex items-start justify-between">
        {STATUS_ORDER.map((status, index) => (
          <div key={status} className="flex items-start flex-1">
            <StatusNode
              status={status}
              label={getStatusLabel(status)}
              isActive={currentIndex === index}
              isPast={currentIndex > index}
              icon={getStatusIcon(status)}
            />
            {index < STATUS_ORDER.length - 1 && (
              <Connector isActive={currentIndex > index} />
            )}
          </div>
        ))}
      </div>

      {/* Session Details */}
      <SessionDetails session={checkoutSession} />
    </div>
  )
}
