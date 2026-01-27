/**
 * TypeScript types for UCP protocol entities
 */

export interface UCPProfile {
  ucp: UCPMetadata;
  signing_keys?: SigningKey[];
}

export interface UCPMetadata {
  version: string;
  services: Record<string, UCPService[]>;
  capabilities: Record<string, UCPCapability[]>;
  payment_handlers: Record<string, UCPPaymentHandler[]>;
}

export interface UCPService {
  version: string;
  spec: string;
  transport: 'rest' | 'mcp' | 'a2a' | 'embedded';
  endpoint?: string;
  schema?: string;
}

export interface UCPCapability {
  version: string;
  spec: string;
  schema: string;
  extends?: string;
  config?: Record<string, unknown>;
}

export interface UCPPaymentHandler {
  id: string;
  version: string;
  spec?: string;
  schema?: string;
  config?: Record<string, unknown>;
}

export interface SigningKey {
  kid: string;
  kty: string;
  crv?: string;
  x?: string;
  y?: string;
  use: string;
  alg: string;
}

export interface CheckoutSession {
  ucp: UCPResponseMetadata;
  id: string;
  status: CheckoutStatus;
  line_items: LineItem[];
  buyer?: Buyer;
  fulfillment?: Fulfillment;
  discounts: Discount[];
  totals?: Total;
  messages: Message[];
  links: Link[];
  continue_url?: string;
  expires_at?: string;
  order?: OrderConfirmation;
  created_at: string;
  updated_at: string;
}

export interface UCPResponseMetadata {
  version: string;
  capabilities: Record<string, { version: string }[]>;
  payment_handlers: Record<string, { id: string; version: string }[]>;
}

export type CheckoutStatus =
  | 'incomplete'
  | 'requires_escalation'
  | 'ready_for_complete'
  | 'complete_in_progress'
  | 'completed'
  | 'canceled';

export interface LineItem {
  id: string;
  product_id: string;
  title: string;
  description?: string;
  image_url?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  currency: string;
}

export interface Buyer {
  email?: string;
  phone?: string;
  first_name?: string;
  last_name?: string;
  billing_address?: PostalAddress;
}

export interface PostalAddress {
  street_address?: string;
  extended_address?: string;
  address_locality?: string;
  address_region?: string;
  postal_code?: string;
  address_country?: string;
  first_name?: string;
  last_name?: string;
}

export interface Fulfillment {
  type: string;
  address?: PostalAddress;
  selected_option_id?: string;
  available_options: FulfillmentOption[];
}

export interface FulfillmentOption {
  id: string;
  title: string;
  description?: string;
  price: number;
  currency: string;
  estimated_delivery?: string;
}

export interface Discount {
  code: string;
  title: string;
  amount: number;
  currency: string;
}

export interface Total {
  subtotal: number;
  discount: number;
  shipping: number;
  tax: number;
  total: number;
  currency: string;
}

export interface Message {
  type: 'error' | 'warning' | 'info';
  code: string;
  content: string;
  severity?: 'recoverable' | 'requires_buyer_input' | 'requires_buyer_review';
}

export interface Link {
  type: string;
  href: string;
  title?: string;
}

export interface OrderConfirmation {
  id: string;
  permalink_url?: string;
  created_at: string;
}

export interface Product {
  id: string;
  title: string;
  description?: string;
  image_url?: string;
  price: number;
  currency: string;
}

export interface ProtocolEvent {
  id: string;
  type: string;
  direction: 'request' | 'response';
  timestamp: string;
  method: string;
  path: string;
  status_code?: number;
  duration_ms?: number;
  body_preview?: string;
  has_ucp: boolean;
  // Educational context - short description for event list
  title?: string;
  description?: string;
  // Detailed commentary for inspector panel
  details?: string;
  ucp_concept?: string;
  learn_more?: string;
}

export interface ProductDisplay {
  id: string;
  title: string;
  description?: string;
  price: string;
  image_url?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  products?: ProductDisplay[];
  show_products?: boolean;
  checkout?: CheckoutSession;
}
