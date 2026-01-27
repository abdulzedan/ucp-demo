"""Protocol event capture and formatting."""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from dataclasses import dataclass, field, asdict


class EventType(str, Enum):
    """Types of UCP protocol events."""

    DISCOVERY = "discovery"
    GET_PRODUCTS = "get_products"
    CREATE_CHECKOUT = "create_checkout"
    GET_CHECKOUT = "get_checkout"
    UPDATE_CHECKOUT = "update_checkout"
    COMPLETE_CHECKOUT = "complete_checkout"
    CANCEL_CHECKOUT = "cancel_checkout"
    TOKENIZE = "tokenize"
    ERROR = "error"
    # Agent thinking events
    AGENT_THINKING = "agent_thinking"
    AGENT_TOOL_CALL = "agent_tool_call"
    AGENT_TOOL_RESULT = "agent_tool_result"


# Educational descriptions for each UCP event type
# Based on UCP specification at https://ucp.dev
UCP_EVENT_INFO: dict[str, dict[str, str]] = {
    "discovery": {
        "title": "UCP Discovery",
        "description": "The Platform fetches the Business's profile from /.well-known/ucp to discover supported capabilities and payment handlers.",
        "details": (
            "This is the foundation of UCP's 'server-selects' architecture where the Business advertises what it supports.\n\n"
            "**What's Discovered:**\n"
            "• **Services**: Available transport bindings (REST, MCP, A2A, EP) with their endpoints and OpenAPI/OpenRPC schemas\n"
            "• **Capabilities**: Features like `dev.ucp.shopping.checkout`, `dev.ucp.shopping.fulfillment`, `dev.ucp.shopping.discount`\n"
            "• **Payment Handlers**: Tokenization specs (e.g., `com.google.pay`, `dev.shopify.shop_pay`) with config for credential acquisition\n"
            "• **Signing Keys**: JWK public keys for webhook verification\n\n"
            "**Capability Negotiation:**\n"
            "The Platform computes the intersection of Business and Platform capabilities. Extensions (like fulfillment) "
            "that declare `extends: dev.ucp.shopping.checkout` are pruned if their parent isn't in the intersection. "
            "This ensures both parties agree on exactly what features are active for the session.\n\n"
            "**Namespace Governance:**\n"
            "Capability names use reverse-domain format (e.g., `dev.ucp.shopping.checkout`). The `dev.ucp.*` namespace "
            "is governed by the UCP body; vendors use their own domains (e.g., `com.shopify.*`)."
        ),
        "ucp_concept": "Discovery & Negotiation",
        "learn_more": "https://ucp.dev/specification/overview/",
    },
    "get_products": {
        "title": "Get Product Catalog",
        "description": "The Platform retrieves the Business's product catalog to understand what's available for purchase.",
        "details": (
            "This is essential for AI agents to match natural language requests ('I want a latte') to specific product IDs.\n\n"
            "**Product Data Structure:**\n"
            "• `id`: Unique product identifier (e.g., 'latte_medium') used in checkout line_items\n"
            "• `title`: Human-readable name displayed to buyers\n"
            "• `description`: Product details for agent context\n"
            "• `price`: Amount in minor units (cents) - e.g., 450 = $4.50\n"
            "• `image_url`: Optional product image for rich UI display\n\n"
            "**Agent Usage:**\n"
            "The AI agent uses this catalog to: (1) present available items to users, (2) validate product requests, "
            "(3) map conversational input to product_ids for add_to_cart operations. Product data from feeds SHOULD "
            "match actual checkout prices to avoid discrepancies.\n\n"
            "**Note:** Product catalog is typically cached by the Platform to avoid repeated fetches during a session."
        ),
        "ucp_concept": "Business Catalog",
        "learn_more": "https://ucp.dev/specification/overview/",
    },
    "create_checkout": {
        "title": "Create Checkout Session",
        "description": "The Platform initiates a new checkout session using the `dev.ucp.shopping.checkout` capability.",
        "details": (
            "This is triggered when a user expresses purchase intent (e.g., 'add a latte to my cart').\n\n"
            "**Request Contains:**\n"
            "• `line_items`: Array of products with `item.id` and `quantity`\n"
            "• `buyer`: Optional buyer info (email, name) if available\n"
            "• `context`: Provisional signals for localization (geo, currency hints)\n"
            "• `payment`: Optional payment instrument selection\n\n"
            "**Response Returns:**\n"
            "• `id`: Unique checkout session identifier for subsequent operations\n"
            "• `status`: Initial state, typically 'incomplete' - see Status Lifecycle below\n"
            "• `line_items`: Enriched with `title`, `price`, `totals` from Business catalog\n"
            "• `totals`: Calculated subtotal, tax, shipping, discounts, total (in minor units)\n"
            "• `messages`: Validation errors/warnings with `severity` indicating who can fix\n"
            "• `payment_handlers`: Available payment methods with tokenization configs\n"
            "• `continue_url`: Handoff URL if buyer input is required\n\n"
            "**Status Lifecycle Start:**\n"
            "```\n"
            "incomplete → requires_escalation → ready_for_complete → complete_in_progress → completed\n"
            "```\n"
            "The Business remains the Merchant of Record (MoR) - they retain financial liability and order ownership."
        ),
        "ucp_concept": "Checkout Capability",
        "learn_more": "https://ucp.dev/specification/checkout/",
    },
    "get_checkout": {
        "title": "Get Checkout State",
        "description": "The Platform retrieves the current state of an existing checkout session.",
        "details": (
            "This is used to refresh the UI, check if requirements are met, or sync after external changes.\n\n"
            "**Response Contains Current State:**\n"
            "• `status`: Current phase - 'incomplete', 'requires_escalation', 'ready_for_complete', 'completed', 'canceled'\n"
            "• `line_items`: Current cart contents with prices and per-item totals\n"
            "• `totals`: Array of totals by type (subtotal, discount, fulfillment, tax, total)\n"
            "• `fulfillment`: Selected shipping/pickup option and address (if Fulfillment extension active)\n"
            "• `discounts`: Applied discount codes with amounts (if Discount extension active)\n"
            "• `messages`: Current validation state - errors that need resolution\n"
            "• `continue_url`: Available for handoff to Business UI if needed\n\n"
            "**Status Interpretation:**\n"
            "• `incomplete`: Missing required info - check `messages` for what's needed\n"
            "• `requires_escalation`: Needs buyer input not available via API - use `continue_url`\n"
            "• `ready_for_complete`: All requirements met - can call Complete Checkout\n"
            "• `completed`: Order placed successfully - check `order` for confirmation\n\n"
            "**TTL:** Sessions typically expire after 6 hours if not completed (per `expires_at`)."
        ),
        "ucp_concept": "Checkout Session",
        "learn_more": "https://ucp.dev/specification/checkout/",
    },
    "update_checkout": {
        "title": "Update Checkout Session",
        "description": "The Platform updates an existing checkout session with cart changes, fulfillment, or discounts.",
        "details": (
            "UCP uses **full replacement** semantics - the Platform MUST send the entire checkout state, not just changes.\n\n"
            "**Common Update Operations:**\n"
            "• **Cart Changes**: Add/remove items, update quantities in `line_items`\n"
            "• **Fulfillment Selection**: Choose shipping option (`selected_option_id`) and provide address\n"
            "• **Discount Codes**: Apply promo codes in `discount_codes` array\n"
            "• **Buyer Info**: Add email, phone, name as required by Business\n\n"
            "**Status Transitions:**\n"
            "```\n"
            "incomplete ──(resolve errors)──► ready_for_complete\n"
            "     │\n"
            "     └──(needs buyer input)──► requires_escalation\n"
            "```\n\n"
            "**Error Processing:**\n"
            "When `messages` contains errors, check `severity`:\n"
            "• `recoverable`: Platform can fix via API (e.g., format phone number)\n"
            "• `requires_buyer_input`: Needs info not available via API → use `continue_url`\n"
            "• `requires_buyer_review`: Buyer must authorize (e.g., high-value order) → use `continue_url`\n\n"
            "**Extension Behavior:**\n"
            "If `dev.ucp.shopping.fulfillment` is active, Business returns `available_options` with shipping methods. "
            "If `dev.ucp.shopping.discount` is active, `discounts` array shows applied codes and savings."
        ),
        "ucp_concept": "Checkout Lifecycle",
        "learn_more": "https://ucp.dev/specification/checkout/",
    },
    "complete_checkout": {
        "title": "Complete Checkout",
        "description": "The Platform finalizes the checkout by submitting payment credentials to create an order.",
        "details": (
            "This is the culmination of the checkout flow and results in order creation.\n\n"
            "**Prerequisites:**\n"
            "• Status MUST be `ready_for_complete` before calling\n"
            "• Payment credential must be acquired from Credential Provider (see Tokenization)\n"
            "• All required fields (buyer info, fulfillment) must be provided\n\n"
            "**Request Contains:**\n"
            "• `payment.instruments[]`: Array with selected payment instrument:\n"
            "  - `handler_id`: Which payment handler to use (from `payment_handlers`)\n"
            "  - `credential`: Opaque token from Credential Provider\n"
            "  - `display`: Card brand, last 4 digits for receipt\n"
            "  - `billing_address`: If required by payment method\n"
            "• `risk_signals`: Optional fraud prevention data (session_id, score)\n\n"
            "**Status Flow:**\n"
            "```\n"
            "ready_for_complete ──(complete called)──► complete_in_progress ──► completed\n"
            "                                                                      │\n"
            "                                              └──(3DS/SCA required)──► requires_escalation\n"
            "```\n\n"
            "**Response on Success:**\n"
            "• `status`: 'completed'\n"
            "• `order.id`: Created order identifier\n"
            "• `order.permalink_url`: Direct link to order confirmation page\n\n"
            "**Payment Flow (Trust Triangle):**\n"
            "Credentials flow Platform → Business → PSP only. Business has legal relationship with PSP. "
            "Platform never touches raw PANs - only opaque tokens. This minimizes PCI-DSS scope for all parties."
        ),
        "ucp_concept": "Payment & Order",
        "learn_more": "https://ucp.dev/specification/checkout/",
    },
    "cancel_checkout": {
        "title": "Cancel Checkout",
        "description": "The Platform cancels an active checkout session, terminating the transaction.",
        "details": (
            "**When to Cancel:**\n"
            "• User explicitly abandons cart\n"
            "• Session timeout/expiry\n"
            "• Unrecoverable errors\n"
            "• User starts new checkout\n\n"
            "**Status Transition:**\n"
            "```\n"
            "any_state ──(cancel)──► canceled\n"
            "```\n\n"
            "**After Cancellation:**\n"
            "• Session becomes invalid - no further operations allowed\n"
            "• Platform should create new checkout if user wants to continue shopping\n"
            "• Business MAY retain session for analytics or expire immediately\n\n"
            "**Note:** Once canceled, the checkout cannot be resumed. "
            "This is a terminal state alongside 'completed'."
        ),
        "ucp_concept": "Checkout Lifecycle",
        "learn_more": "https://ucp.dev/specification/checkout/",
    },
    "tokenize": {
        "title": "Payment Tokenization",
        "description": "The Platform acquires a payment credential from a Credential Provider (e.g., Google Pay, Shop Pay).",
        "details": (
            "This is the 'Acquisition' phase of UCP's 3-step payment flow: Negotiation → Acquisition → Completion.\n\n"
            "**The Trust Triangle:**\n"
            "```\n"
            "         Credential Provider (Google Pay, Shop Pay)\n"
            "                    /           \\\n"
            "           (token)  /             \\  (legal relationship)\n"
            "                   /               \\\n"
            "            Platform ─────────────► Business ─────► PSP\n"
            "                    (opaque token)        (decrypt & charge)\n"
            "```\n\n"
            "**How It Works:**\n"
            "1. Business advertises `payment_handlers` in their profile with tokenization `config`\n"
            "2. Platform reads handler config (public keys, merchant IDs, allowed networks)\n"
            "3. Platform calls Credential Provider's API/SDK with Business's config\n"
            "4. Credential Provider returns encrypted token (e.g., `shoppay_tok_xxx`, Google Pay blob)\n"
            "5. Platform submits opaque token to Business in Complete Checkout\n"
            "6. Business decrypts using their PSP relationship and charges\n\n"
            "**PCI-DSS Scope Minimization:**\n"
            "• Platform: Never sees raw card data - only handles tokens\n"
            "• Business: Uses PSP tokenization - delegates credential handling\n"
            "• Raw PANs only exist within PCI-certified Credential Provider and PSP\n\n"
            "**Handler Examples:**\n"
            "• `com.google.pay`: Google Pay tokenization\n"
            "• `dev.shopify.shop_pay`: Shop Pay tokenization\n"
            "• `com.example.tokenizer`: Direct PSP tokenization"
        ),
        "ucp_concept": "Payment Handler",
        "learn_more": "https://ucp.dev/specification/overview/#payment-architecture",
    },
    "error": {
        "title": "Error",
        "description": "An error occurred during a UCP operation with structured severity levels.",
        "details": (
            "UCP uses structured error messages with severity levels to indicate who can resolve the issue.\n\n"
            "**Message Structure:**\n"
            "• `type`: 'error', 'warning', or 'info'\n"
            "• `code`: Machine-readable error code (e.g., 'missing', 'invalid_phone', 'requires_3ds')\n"
            "• `path`: JSONPath to affected field (e.g., '$.buyer.email', '$.fulfillment.address')\n"
            "• `content`: Human-readable description\n"
            "• `severity`: Who can fix this error\n\n"
            "**Severity Levels:**\n"
            "• `recoverable`: Platform can fix via Update Checkout API\n"
            "  → Example: Reformat phone number, add missing email\n"
            "• `requires_buyer_input`: Needs info not available via API\n"
            "  → Example: Select delivery window, custom options\n"
            "  → Platform MUST hand off via `continue_url`\n"
            "• `requires_buyer_review`: Buyer authorization required\n"
            "  → Example: High-value order verification, first purchase policy\n"
            "  → Platform MUST hand off via `continue_url`\n\n"
            "**Error Processing Algorithm:**\n"
            "1. Filter messages where `type` = 'error'\n"
            "2. Partition by severity\n"
            "3. Attempt to resolve all `recoverable` errors first\n"
            "4. Call Update Checkout and re-evaluate\n"
            "5. If `requires_*` errors remain, initiate handoff\n\n"
            "**Status Implications:**\n"
            "`requires_buyer_input` and `requires_buyer_review` errors cause `status: requires_escalation`."
        ),
        "ucp_concept": "Error Handling",
        "learn_more": "https://ucp.dev/specification/checkout/",
    },
    # Agent thinking events
    "agent_thinking": {
        "title": "Agent Thinking",
        "description": "The AI agent is processing the user's request and deciding what action to take.",
        "details": (
            "The agent analyzes the user's message and determines the appropriate response.\n\n"
            "**Decision Process:**\n"
            "1. Parse user intent from natural language\n"
            "2. Match intent to available tools (show_menu, add_to_cart, etc.)\n"
            "3. Gather required parameters from context or conversation\n"
            "4. Execute the appropriate UCP operations\n"
            "5. Format response for the user"
        ),
        "ucp_concept": "Agentic Commerce",
        "learn_more": "https://ucp.dev/specification/overview/",
    },
    "agent_tool_call": {
        "title": "Agent Tool Call",
        "description": "The agent is invoking a tool to perform a UCP operation.",
        "details": (
            "Tools are the agent's interface to UCP capabilities.\n\n"
            "**Available Tools:**\n"
            "• `show_menu`: Fetch and display product catalog\n"
            "• `add_to_cart`: Create/update checkout with items\n"
            "• `view_cart`: Get current checkout state\n"
            "• `select_shipping`: Choose fulfillment option\n"
            "• `apply_discount`: Apply promo code\n"
            "• `complete_checkout`: Finalize order with payment\n\n"
            "Each tool call triggers corresponding UCP API operations."
        ),
        "ucp_concept": "Platform Tools",
        "learn_more": "https://ucp.dev/specification/overview/",
    },
    "agent_tool_result": {
        "title": "Agent Tool Result",
        "description": "The tool has returned a result that the agent will use to formulate a response.",
        "details": (
            "Tool results contain structured data from UCP operations.\n\n"
            "**Result Processing:**\n"
            "• Success responses include UCP data (products, checkout state)\n"
            "• Error responses include messages with severity levels\n"
            "• Agent interprets results to provide helpful user responses\n"
            "• State is updated based on operation outcomes"
        ),
        "ucp_concept": "Response Handling",
        "learn_more": "https://ucp.dev/specification/overview/",
    },
}


class EventDirection(str, Enum):
    """Direction of the event."""

    REQUEST = "request"
    RESPONSE = "response"


@dataclass
class ProtocolEvent:
    """A captured UCP protocol event."""

    id: str
    type: EventType
    direction: EventDirection
    timestamp: str
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] | None = None
    status_code: int | None = None
    duration_ms: float | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class EventStore:
    """In-memory store for protocol events."""

    def __init__(self, max_events: int = 100):
        """Initialize the event store.

        Args:
            max_events: Maximum number of events to keep
        """
        self.max_events = max_events
        self._events: list[ProtocolEvent] = []
        self._subscribers: list = []
        self._event_counter = 0

    def add_event(self, event: ProtocolEvent) -> None:
        """Add an event to the store."""
        self._events.append(event)

        # Trim if over max
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events :]

        # Notify subscribers
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception:
                pass

    def get_events(self, limit: int = 50) -> list[ProtocolEvent]:
        """Get recent events."""
        return self._events[-limit:]

    def clear(self) -> None:
        """Clear all events."""
        self._events = []

    def subscribe(self, callback) -> None:
        """Subscribe to new events.

        Prevents duplicate subscriptions (important for hot-reload).
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback) -> None:
        """Unsubscribe from events."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def next_id(self) -> str:
        """Generate next event ID."""
        self._event_counter += 1
        return f"evt_{self._event_counter:06d}"


# Global event store
event_store = EventStore()


def capture_request(
    event_type: EventType,
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> str:
    """Capture a request event and return its ID."""
    event = ProtocolEvent(
        id=event_store.next_id(),
        type=event_type,
        direction=EventDirection.REQUEST,
        timestamp=datetime.now(timezone.utc).isoformat(),
        method=method,
        path=path,
        headers=headers or {},
        body=body,
    )
    event_store.add_event(event)
    return event.id


def capture_response(
    request_id: str,
    event_type: EventType,
    method: str,
    path: str,
    status_code: int,
    body: dict[str, Any] | None = None,
    duration_ms: float | None = None,
) -> None:
    """Capture a response event."""
    event = ProtocolEvent(
        id=f"{request_id}_resp",
        type=event_type,
        direction=EventDirection.RESPONSE,
        timestamp=datetime.now(timezone.utc).isoformat(),
        method=method,
        path=path,
        status_code=status_code,
        body=body,
        duration_ms=duration_ms,
    )
    event_store.add_event(event)


def format_event_for_display(event: ProtocolEvent) -> dict:
    """Format an event for display in the visualizer."""
    event_info = UCP_EVENT_INFO.get(event.type.value, {})

    return {
        "id": event.id,
        "type": event.type.value,
        "direction": event.direction.value,
        "timestamp": event.timestamp,
        "method": event.method,
        "path": event.path,
        "status_code": event.status_code,
        "duration_ms": event.duration_ms,
        "body_preview": json.dumps(event.body) if event.body else None,
        "has_ucp": _has_ucp_metadata(event.body) if event.body else False,
        # Educational context - short description for event list
        "title": event_info.get("title", event.type.value),
        "description": event_info.get("description", ""),
        # Detailed commentary for inspector panel
        "details": event_info.get("details", ""),
        "ucp_concept": event_info.get("ucp_concept", ""),
        "learn_more": event_info.get("learn_more", ""),
    }


def _get_body_preview(body: dict, max_length: int = 100) -> str:
    """Get a preview of the body."""
    text = json.dumps(body)
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def _has_ucp_metadata(body: dict) -> bool:
    """Check if the body contains UCP metadata."""
    return "ucp" in body


# Agent thinking event helpers
def capture_agent_thinking(message: str, session_id: str = "default") -> str:
    """Capture an agent thinking event."""
    event = ProtocolEvent(
        id=event_store.next_id(),
        type=EventType.AGENT_THINKING,
        direction=EventDirection.REQUEST,
        timestamp=datetime.now(timezone.utc).isoformat(),
        method="THINK",
        path=f"/agent/{session_id}",
        body={"message": message},
    )
    event_store.add_event(event)
    return event.id


def capture_agent_tool_call(
    tool_name: str,
    args: dict[str, Any],
    session_id: str = "default",
) -> str:
    """Capture an agent tool call event."""
    event = ProtocolEvent(
        id=event_store.next_id(),
        type=EventType.AGENT_TOOL_CALL,
        direction=EventDirection.REQUEST,
        timestamp=datetime.now(timezone.utc).isoformat(),
        method="CALL",
        path=f"/agent/tools/{tool_name}",
        body={"tool": tool_name, "args": args},
    )
    event_store.add_event(event)
    return event.id


def capture_agent_tool_result(
    tool_call_id: str,
    tool_name: str,
    result: dict[str, Any] | str,
    success: bool = True,
) -> None:
    """Capture an agent tool result event."""
    event = ProtocolEvent(
        id=f"{tool_call_id}_result",
        type=EventType.AGENT_TOOL_RESULT,
        direction=EventDirection.RESPONSE,
        timestamp=datetime.now(timezone.utc).isoformat(),
        method="RESULT",
        path=f"/agent/tools/{tool_name}",
        status_code=200 if success else 500,
        body={"tool": tool_name, "result": result, "success": success},
    )
    event_store.add_event(event)
