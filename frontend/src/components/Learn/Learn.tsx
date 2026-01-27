import { BookOpen, ExternalLink, CheckCircle, Package, CreditCard, Zap, Shield } from 'lucide-react'

interface LearnProps {
  activeSection?: string
}

const concepts = [
  {
    id: 'ucp-overview',
    icon: <Zap className="w-5 h-5" />,
    title: 'What is UCP?',
    description: 'Universal Commerce Protocol (UCP) is an open standard that enables interoperability between commerce platforms, merchants, and payment providers.',
    details: [
      'Standardized data types for commerce transactions',
      'Capability negotiation between client and merchant',
      'Transport-agnostic (REST, A2A, MCP)',
      'Extensible with modular capabilities',
    ],
    link: 'https://ucp.dev',
  },
  {
    id: 'discovery',
    icon: <Shield className="w-5 h-5" />,
    title: 'Capability Discovery',
    description: 'Before any transaction, platforms discover what capabilities a merchant supports by fetching their UCP profile.',
    details: [
      'Profile served at /.well-known/ucp',
      'Lists supported capabilities (checkout, fulfillment, discounts)',
      'Declares payment handlers and versions',
      'Enables client/merchant capability negotiation',
    ],
    link: 'https://ucp.dev/specification/overview/',
  },
  {
    id: 'checkout',
    icon: <CheckCircle className="w-5 h-5" />,
    title: 'Checkout Lifecycle',
    description: 'UCP defines a state machine for checkout sessions with clear status transitions.',
    details: [
      'incomplete - Missing required information',
      'requires_escalation - Needs buyer input',
      'ready_for_complete - All requirements met',
      'complete_in_progress - Payment processing',
      'completed - Order confirmed',
      'canceled - Session canceled',
    ],
    link: 'https://ucp.dev/specs/shopping/checkout',
  },
  {
    id: 'fulfillment',
    icon: <Package className="w-5 h-5" />,
    title: 'Fulfillment Extension',
    description: 'The fulfillment capability extends checkout with shipping and delivery options.',
    details: [
      'Available shipping options with prices',
      'Delivery time estimates',
      'Address collection and validation',
      'Extends the base checkout schema',
    ],
    link: 'https://ucp.dev/specs/shopping/fulfillment',
  },
  {
    id: 'payment',
    icon: <CreditCard className="w-5 h-5" />,
    title: 'Payment Handlers',
    description: 'UCP separates payment tokenization from the checkout flow to keep sensitive data secure.',
    details: [
      'Payment handlers are declared in UCP profile',
      'Tokenization happens outside UCP flow',
      'Only tokens passed to checkout completion',
      'Reduces PCI scope for merchants',
    ],
    link: 'https://ucp.dev/specs/shopping/payment',
  },
]

export default function Learn({ activeSection }: LearnProps) {
  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <BookOpen className="w-6 h-6 text-purple-600" />
          <h2 className="text-xl font-semibold text-gray-900">Learn UCP</h2>
        </div>
        <p className="text-sm text-gray-600">
          Understand the key concepts of the Universal Commerce Protocol as you use this demo.
        </p>
      </div>

      <div className="space-y-4">
        {concepts.map((concept) => (
          <div
            key={concept.id}
            className={`p-4 rounded-lg border transition-all ${
              activeSection === concept.id
                ? 'bg-purple-50 border-purple-300 ring-2 ring-purple-200'
                : 'bg-white border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg ${
                activeSection === concept.id ? 'bg-purple-200 text-purple-700' : 'bg-gray-100 text-gray-600'
              }`}>
                {concept.icon}
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{concept.title}</h3>
                <p className="text-sm text-gray-600 mt-1">{concept.description}</p>

                <ul className="mt-3 space-y-1">
                  {concept.details.map((detail, idx) => (
                    <li key={idx} className="text-xs text-gray-500 flex items-start gap-2">
                      <span className="text-purple-500 mt-0.5">-</span>
                      <span>{detail}</span>
                    </li>
                  ))}
                </ul>

                <a
                  href={concept.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mt-3 text-xs text-purple-600 hover:text-purple-800 hover:underline"
                >
                  Learn more
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
        <h3 className="font-medium text-gray-900 mb-2">Try It Yourself</h3>
        <p className="text-sm text-gray-600">
          Use the chat on the left to interact with the shopping agent. Watch the Protocol Events
          tab to see UCP messages flowing in real-time, with explanations of each operation.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="px-2 py-1 text-xs bg-white rounded border border-gray-200">
            "Show menu"
          </span>
          <span className="px-2 py-1 text-xs bg-white rounded border border-gray-200">
            "Add a latte"
          </span>
          <span className="px-2 py-1 text-xs bg-white rounded border border-gray-200">
            "Standard delivery"
          </span>
          <span className="px-2 py-1 text-xs bg-white rounded border border-gray-200">
            "Use code DEMO20"
          </span>
          <span className="px-2 py-1 text-xs bg-white rounded border border-gray-200">
            "Checkout"
          </span>
        </div>
      </div>
    </div>
  )
}
