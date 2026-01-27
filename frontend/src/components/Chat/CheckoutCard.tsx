import { useState } from 'react'
import { ShoppingCart, Package, Truck, Tag, CreditCard, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { CheckoutSession } from '../../types/ucp'

interface CheckoutCardProps {
  checkout: CheckoutSession
  onCompleteCheckout?: () => void
}

function formatCurrency(amount: number, currency: string = 'USD'): string {
  return `$${(amount / 100).toFixed(2)}`
}

function getStatusBadge(status: string) {
  const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
    incomplete: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Incomplete' },
    requires_escalation: { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Action Required' },
    ready_for_complete: { bg: 'bg-green-100', text: 'text-green-700', label: 'Ready to Complete' },
    complete_in_progress: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Processing...' },
    completed: { bg: 'bg-green-100', text: 'text-green-700', label: 'Order Confirmed' },
    canceled: { bg: 'bg-red-100', text: 'text-red-700', label: 'Canceled' },
  }
  const config = statusConfig[status] || { bg: 'bg-gray-100', text: 'text-gray-700', label: status }
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  )
}

export default function CheckoutCard({ checkout, onCompleteCheckout }: CheckoutCardProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const isCompleted = checkout.status === 'completed'
  const isReady = checkout.status === 'ready_for_complete'

  return (
    <div className="mt-3 bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden max-w-md">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          {isCompleted ? (
            <CheckCircle className="w-5 h-5 text-green-500" />
          ) : (
            <ShoppingCart className="w-5 h-5 text-blue-500" />
          )}
          <span className="font-semibold text-gray-900">
            {isCompleted ? 'Order Confirmed' : 'Checkout Summary'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {getStatusBadge(checkout.status)}
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Order ID if completed */}
          {checkout.order?.id && (
            <div className="px-4 py-2 bg-green-50 border-b border-green-100">
              <p className="text-sm text-green-700">
                <span className="font-medium">Order ID:</span> {checkout.order.id}
              </p>
            </div>
          )}

          {/* Line Items */}
          <div className="px-4 py-3 space-y-3">
            {checkout.line_items.map((item) => (
              <div key={item.id} className="flex items-center gap-3">
                {item.image_url && (
                  <img
                    src={item.image_url}
                    alt={item.title}
                    className="w-12 h-12 object-cover rounded-md"
                  />
                )}
                <div className="flex-grow min-w-0">
                  <p className="font-medium text-gray-900 text-sm truncate">{item.title}</p>
                  <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                </div>
                <p className="text-sm font-medium text-gray-900">
                  {formatCurrency(item.total_price, item.currency)}
                </p>
              </div>
            ))}
          </div>

          {/* Fulfillment */}
          {checkout.fulfillment?.selected_option_id && (
            <div className="px-4 py-2 border-t border-gray-100">
              <div className="flex items-center gap-2 text-sm">
                {checkout.fulfillment.selected_option_id === 'pickup' ? (
                  <Package className="w-4 h-4 text-gray-400" />
                ) : (
                  <Truck className="w-4 h-4 text-gray-400" />
                )}
                <span className="text-gray-600">
                  {checkout.fulfillment.available_options.find(
                    o => o.id === checkout.fulfillment?.selected_option_id
                  )?.title || checkout.fulfillment.selected_option_id}
                </span>
              </div>
            </div>
          )}

          {/* Discounts */}
          {checkout.discounts.length > 0 && (
            <div className="px-4 py-2 border-t border-gray-100">
              {checkout.discounts.map((discount) => (
                <div key={discount.code} className="flex items-center gap-2 text-sm">
                  <Tag className="w-4 h-4 text-green-500" />
                  <span className="text-green-600 font-medium">{discount.code}</span>
                  <span className="text-green-600">-{formatCurrency(discount.amount, discount.currency)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Totals */}
          {checkout.totals && (
            <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 space-y-1">
              <div className="flex justify-between text-sm text-gray-600">
                <span>Subtotal</span>
                <span>{formatCurrency(checkout.totals.subtotal, checkout.totals.currency)}</span>
              </div>
              {checkout.totals.discount > 0 && (
                <div className="flex justify-between text-sm text-green-600">
                  <span>Discount</span>
                  <span>-{formatCurrency(checkout.totals.discount, checkout.totals.currency)}</span>
                </div>
              )}
              {checkout.totals.shipping > 0 && (
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Shipping</span>
                  <span>{formatCurrency(checkout.totals.shipping, checkout.totals.currency)}</span>
                </div>
              )}
              {checkout.totals.tax > 0 && (
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Tax</span>
                  <span>{formatCurrency(checkout.totals.tax, checkout.totals.currency)}</span>
                </div>
              )}
              <div className="flex justify-between text-base font-bold text-gray-900 pt-2 border-t border-gray-200">
                <span>Total</span>
                <span>{formatCurrency(checkout.totals.total, checkout.totals.currency)}</span>
              </div>
            </div>
          )}

          {/* Complete Button */}
          {isReady && onCompleteCheckout && (
            <div className="px-4 py-3 border-t border-gray-200">
              <button
                onClick={onCompleteCheckout}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 transition-colors"
              >
                <CreditCard className="w-4 h-4" />
                Complete Order
              </button>
            </div>
          )}

          {/* Checkout ID */}
          <div className="px-4 py-2 border-t border-gray-100">
            <p className="text-xs text-gray-400 text-center">
              Checkout ID: {checkout.id}
            </p>
          </div>
        </>
      )}
    </div>
  )
}
