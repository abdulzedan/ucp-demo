"""AI Shopping Agent - Conversational commerce using UCP and Google ADK.

This agent follows Google ADK patterns with proper ToolContext-based state management
and dynamically retrieves data from the UCP client instead of hardcoding values.
"""

import logging
import os
from typing import Any

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from backend.platform.ucp_client import UCPClient
from backend.schemas.checkout import CheckoutStatus
from backend.visualizer.events import (
    capture_request,
    capture_response,
    capture_agent_tool_call,
    capture_agent_tool_result,
    EventType,
)

# State keys following ADK patterns (prefix with user: for session-scoped data)
ADK_USER_CHECKOUT_ID = "user:checkout_id"
ADK_PRODUCTS_CACHE = "user:products_cache"
ADK_UCP_DISCOVERED = "user:ucp_discovered"
ADK_LATEST_TOOL_RESULT = "temp:LATEST_TOOL_RESULT"

# Response keys for UCP data
UCP_CHECKOUT_KEY = "a2a.ucp.checkout"
UCP_PRODUCTS_KEY = "a2a.ucp.products"

logger = logging.getLogger(__name__)

# Global UCP client instance (initialized by ShoppingAgentService)
_ucp_client: UCPClient | None = None

# Track which events have been emitted this session to avoid duplicates
_emitted_events: set[str] = set()


def _emit_event(event_type: EventType, method: str, path: str, request_body: dict | None = None, response_body: dict | None = None, status_code: int = 200) -> None:
    """Emit a protocol event for visualization."""
    import time
    start = time.time()
    request_id = capture_request(
        event_type=event_type,
        method=method,
        path=path,
        headers={"X-UCP-Agent": "cymbal_coffee_agent"},
        body=request_body,
    )
    duration_ms = (time.time() - start) * 1000
    capture_response(
        request_id=request_id,
        event_type=event_type,
        method=method,
        path=path,
        status_code=status_code,
        body=response_body,
        duration_ms=round(duration_ms, 2),
    )


def _reset_emitted_events() -> None:
    """Reset the emitted events tracker (call on session reset)."""
    global _emitted_events
    _emitted_events = set()


def _get_ucp_client() -> UCPClient:
    """Get the global UCP client instance."""
    global _ucp_client
    if _ucp_client is None:
        _ucp_client = UCPClient("http://localhost:8000")
    return _ucp_client


def _create_error_response(message: str) -> dict:
    """Create a standardized error response."""
    return {"message": message, "status": "error"}


# ============================================================================
# TOOL DEFINITIONS
# Tools follow ADK pattern: sync functions with ToolContext as first parameter
# ============================================================================


def show_menu(tool_context: ToolContext) -> dict:
    """Show the product menu/catalog to the customer.

    Returns all available products from the Cymbal Coffee Shop catalog.
    Use this when the user asks to see products, menu, or what's available.

    Args:
        tool_context: The tool context for the current request.

    Returns:
        dict: Product catalog with available items.
    """
    global _emitted_events
    print(f"[AGENT] show_menu called, _emitted_events={_emitted_events}")
    try:
        client = _get_ucp_client()

        # Ensure discovery (only emit event once per session)
        if not client._discovered:
            client.discover()

        # Emit discovery event only once
        if "discovery" not in _emitted_events:
            _emitted_events.add("discovery")
            print("[AGENT] Emitting discovery event (first time)")
            _emit_event(
                EventType.DISCOVERY,
                "GET",
                "/.well-known/ucp",
                response_body={"capabilities": client.get_capabilities()},
            )
        else:
            print("[AGENT] Skipping discovery event (already emitted)")

        # Get products (use cache if available, only emit event once)
        products = tool_context.state.get(ADK_PRODUCTS_CACHE)
        if not products:
            products = client.get_products()
            tool_context.state[ADK_PRODUCTS_CACHE] = products

        # Emit products event only once
        if "products" not in _emitted_events:
            _emitted_events.add("products")
            print("[AGENT] Emitting products event (first time)")
            _emit_event(
                EventType.GET_PRODUCTS,
                "GET",
                "/api/v1/products",
                response_body={"products": products},
            )
        else:
            print("[AGENT] Skipping products event (already emitted)")

        # Format products for display
        product_list = []
        for p in products:
            product_list.append({
                "id": p["id"],
                "title": p["title"],
                "description": p.get("description"),
                "price": f"${p['price'] / 100:.2f}",
            })

        return {
            UCP_PRODUCTS_KEY: products,  # Full data for UI
            "products": product_list,  # Formatted for agent
            "message": "Here are our available products.",
            "status": "success",
        }
    except Exception:
        logging.exception("Error fetching products")
        return _create_error_response("Could not fetch products. Please try again.")


def add_to_cart(
    tool_context: ToolContext,
    product_id: str,
    quantity: int = 1,
) -> dict:
    """Add a product to the shopping cart.

    Use this when the user wants to add an item to their cart.
    The product_id should match an ID from the catalog (use show_menu first
    if you need to see available products).

    Args:
        tool_context: The tool context for the current request.
        product_id: The product ID to add (e.g., 'latte_medium', 'espresso_single').
        quantity: Number of items to add (default 1).

    Returns:
        dict: Updated checkout with cart contents and available shipping options.
    """
    client = _get_ucp_client()
    checkout_id = tool_context.state.get(ADK_USER_CHECKOUT_ID)

    try:
        # Get current cart items if checkout exists
        current_items = []
        if checkout_id:
            try:
                checkout = client.get_checkout(checkout_id)
                current_items = [
                    {"product_id": li.product_id, "quantity": li.quantity}
                    for li in checkout.line_items
                ]
            except Exception:
                checkout_id = None
                tool_context.state[ADK_USER_CHECKOUT_ID] = None

        # Merge items
        item_map = {item["product_id"]: item["quantity"] for item in current_items}
        item_map[product_id] = item_map.get(product_id, 0) + quantity

        merged_items = [
            {"product_id": pid, "quantity": qty}
            for pid, qty in item_map.items()
        ]

        # Create or update checkout
        if checkout_id:
            checkout = client.update_checkout(
                checkout_id,
                line_items=merged_items,
            )
            # Emit update event
            _emit_event(
                EventType.UPDATE_CHECKOUT,
                "PUT",
                f"/api/v1/checkout-sessions/{checkout_id}",
                request_body={"line_items": merged_items},
                response_body=checkout.model_dump(mode="json"),
            )
        else:
            checkout = client.create_checkout(line_items=merged_items)
            tool_context.state[ADK_USER_CHECKOUT_ID] = checkout.id
            # Emit create event
            _emit_event(
                EventType.CREATE_CHECKOUT,
                "POST",
                "/api/v1/checkout-sessions",
                request_body={"line_items": merged_items},
                response_body=checkout.model_dump(mode="json"),
            )

        # Format response with DYNAMIC fulfillment options from checkout
        response = {
            UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
            "status": "success",
            "items": [
                {
                    "title": li.title,
                    "quantity": li.quantity,
                    "price": f"${li.total_price / 100:.2f}",
                }
                for li in checkout.line_items
            ],
            "subtotal": f"${checkout.totals.subtotal / 100:.2f}" if checkout.totals else None,
        }

        # Include available shipping options dynamically from checkout
        if checkout.fulfillment and checkout.fulfillment.available_options:
            response["shipping_options"] = [
                {
                    "id": opt.id,
                    "title": opt.title,
                    "price": f"${opt.price / 100:.2f}" if opt.price > 0 else "Free",
                    "delivery": opt.estimated_delivery,
                }
                for opt in checkout.fulfillment.available_options
            ]

        return response

    except Exception:
        logging.exception("Error adding to cart")
        return _create_error_response("Could not add item to cart. Please try again.")


def view_cart(tool_context: ToolContext) -> dict:
    """View the current shopping cart contents and available options.

    Returns the current checkout state including items, totals,
    available shipping options, and any applied discounts.
    Use this when the user asks to see their cart or when you need
    to check available shipping options.

    Args:
        tool_context: The tool context for the current request.

    Returns:
        dict: Current cart state with items, totals, and available options.
    """
    checkout_id = tool_context.state.get(ADK_USER_CHECKOUT_ID)

    if not checkout_id:
        return {
            "status": "empty",
            "message": "Your cart is empty. Use show_menu to see available products.",
        }

    try:
        client = _get_ucp_client()
        checkout = client.get_checkout(checkout_id)
        # Emit get checkout event
        _emit_event(
            EventType.GET_CHECKOUT,
            "GET",
            f"/api/v1/checkout-sessions/{checkout_id}",
            response_body=checkout.model_dump(mode="json"),
        )
    except Exception as e:
        return {"error": str(e), "status": "error"}

    result = {
        UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
        "checkout_id": checkout.id,
        "checkout_status": checkout.status.value,
        "status": "success",
        "items": [
            {
                "title": li.title,
                "quantity": li.quantity,
                "price": f"${li.total_price / 100:.2f}",
            }
            for li in checkout.line_items
        ],
    }

    if checkout.totals:
        result["totals"] = {
            "subtotal": f"${checkout.totals.subtotal / 100:.2f}",
            "discount": f"${checkout.totals.discount / 100:.2f}",
            "shipping": f"${checkout.totals.shipping / 100:.2f}",
            "tax": f"${checkout.totals.tax / 100:.2f}",
            "total": f"${checkout.totals.total / 100:.2f}",
        }

    # IMPORTANT: Include available shipping options dynamically
    if checkout.fulfillment and checkout.fulfillment.available_options:
        result["shipping_options"] = [
            {
                "id": opt.id,
                "title": opt.title,
                "price": f"${opt.price / 100:.2f}" if opt.price > 0 else "Free",
                "delivery": opt.estimated_delivery,
            }
            for opt in checkout.fulfillment.available_options
        ]
        result["selected_shipping"] = checkout.fulfillment.selected_option_id

    if checkout.discounts:
        result["discounts"] = [
            {"code": d.code, "title": d.title, "amount": f"${d.amount / 100:.2f}"}
            for d in checkout.discounts
        ]

    if checkout.messages:
        result["messages"] = [
            {"type": m.type.value, "content": m.content}
            for m in checkout.messages
        ]

    return result


def select_shipping(tool_context: ToolContext, option_id: str) -> dict:
    """Select a shipping/delivery option.

    Use this when the user mentions shipping, delivery, pickup, or refers
    to options by number (1st, 2nd, 3rd) or name.
    IMPORTANT: Call view_cart first to see available options if the user
    references options by number.

    Args:
        tool_context: The tool context for the current request.
        option_id: The shipping option ID from the available_options list.

    Returns:
        dict: Updated checkout with selected shipping and new totals.
    """
    checkout_id = tool_context.state.get(ADK_USER_CHECKOUT_ID)

    if not checkout_id:
        return _create_error_response("No active checkout. Add items to your cart first.")

    try:
        client = _get_ucp_client()
        current = client.get_checkout(checkout_id)

        fulfillment_data = {"selected_option_id": option_id}

        # For non-pickup options, provide a demo address if none exists
        if option_id != "pickup":
            if current.fulfillment and current.fulfillment.address:
                fulfillment_data["address"] = current.fulfillment.address.model_dump()
            else:
                # Default demo address for delivery options
                fulfillment_data["address"] = {
                    "street_address": "123 Demo Street",
                    "address_locality": "San Francisco",
                    "address_region": "CA",
                    "postal_code": "94102",
                    "address_country": "US",
                }

        checkout = client.update_checkout(
            checkout_id,
            line_items=[
                {"product_id": li.product_id, "quantity": li.quantity}
                for li in current.line_items
            ],
            fulfillment=fulfillment_data,
            discount_codes=[d.code for d in current.discounts],
        )
        # Emit update event for shipping selection
        _emit_event(
            EventType.UPDATE_CHECKOUT,
            "PUT",
            f"/api/v1/checkout-sessions/{checkout_id}",
            request_body={"fulfillment": fulfillment_data},
            response_body=checkout.model_dump(mode="json"),
        )

        # Get the selected option details dynamically
        selected_option = None
        if checkout.fulfillment and checkout.fulfillment.available_options:
            for opt in checkout.fulfillment.available_options:
                if opt.id == option_id:
                    selected_option = opt
                    break

        return {
            UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
            "status": "success",
            "selected_option": option_id,
            "selected_option_title": selected_option.title if selected_option else option_id,
            "selected_option_delivery": selected_option.estimated_delivery if selected_option else None,
            "shipping_cost": f"${checkout.totals.shipping / 100:.2f}" if checkout.totals else None,
            "new_total": f"${checkout.totals.total / 100:.2f}" if checkout.totals else None,
            "checkout_status": checkout.status.value,
        }

    except Exception:
        logging.exception("Error selecting shipping")
        return _create_error_response("Could not update shipping. Please try again.")


def apply_discount(tool_context: ToolContext, code: str) -> dict:
    """Apply a discount code to the order.

    Use this when the user mentions a promo code, discount code, or coupon.

    Args:
        tool_context: The tool context for the current request.
        code: The discount code to apply.

    Returns:
        dict: Result indicating success or failure with updated totals.
    """
    checkout_id = tool_context.state.get(ADK_USER_CHECKOUT_ID)

    if not checkout_id:
        return _create_error_response("No active checkout. Add items first.")

    try:
        client = _get_ucp_client()
        current = client.get_checkout(checkout_id)

        # Check if already applied
        existing_codes = [d.code for d in current.discounts]
        if code.upper() in [c.upper() for c in existing_codes]:
            return {"status": "already_applied", "message": f"Code {code} already applied"}

        # Update with new discount code
        checkout = client.update_checkout(
            checkout_id,
            line_items=[
                {"product_id": li.product_id, "quantity": li.quantity}
                for li in current.line_items
            ],
            fulfillment={
                "selected_option_id": current.fulfillment.selected_option_id,
                "address": current.fulfillment.address.model_dump() if current.fulfillment.address else None,
            } if current.fulfillment else None,
            discount_codes=existing_codes + [code],
        )

        # Emit update event for discount
        _emit_event(
            EventType.UPDATE_CHECKOUT,
            "PUT",
            f"/api/v1/checkout-sessions/{checkout_id}",
            request_body={"discount_codes": existing_codes + [code]},
            response_body=checkout.model_dump(mode="json"),
        )

        # Check if the code was applied
        applied = [d for d in checkout.discounts if d.code.upper() == code.upper()]
        if applied:
            return {
                UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
                "status": "applied",
                "discount": {
                    "code": applied[0].code,
                    "title": applied[0].title,
                    "amount": f"${applied[0].amount / 100:.2f}",
                },
                "new_total": f"${checkout.totals.total / 100:.2f}" if checkout.totals else None,
            }
        else:
            return {"status": "invalid", "message": f"Code {code} is not valid"}

    except Exception:
        logging.exception("Error applying discount")
        return _create_error_response("Could not apply discount. Please try again.")


def complete_checkout(tool_context: ToolContext) -> dict:
    """Complete the checkout and place the order.

    This will finalize the order and process payment.
    If no shipping option is selected, pickup will be auto-selected.

    Args:
        tool_context: The tool context for the current request.

    Returns:
        dict: Order confirmation with order ID or error if not ready.
    """
    checkout_id = tool_context.state.get(ADK_USER_CHECKOUT_ID)

    if not checkout_id:
        return _create_error_response("No active checkout")

    try:
        client = _get_ucp_client()
        current = client.get_checkout(checkout_id)

        # Auto-select pickup if no shipping selected
        if not current.fulfillment or not current.fulfillment.selected_option_id:
            select_shipping(tool_context, "pickup")
            current = client.get_checkout(checkout_id)

        if current.status != CheckoutStatus.READY_FOR_COMPLETE:
            return {
                "error": "Checkout is not ready to complete",
                "status": current.status.value,
                "messages": [m.content for m in current.messages if m.type.value == "error"],
            }

        # Get a mock payment token
        handlers = client.get_payment_handlers()
        if not handlers:
            return _create_error_response("No payment handlers available")

        handler = handlers[0]
        token_response = client.tokenize_payment(
            handler["id"],
            {"demo": True},
        )
        # Emit tokenization event
        _emit_event(
            EventType.TOKENIZE,
            "POST",
            "/api/v1/tokenize",
            request_body={"handler_id": handler["id"]},
            response_body=token_response,
        )

        # Complete the checkout
        payment_data = {
            "instruments": [
                {
                    "id": "pm_demo",
                    "handler_id": handler["id"],
                    "type": "card",
                    "selected": True,
                    "display": {"brand": "visa", "last_digits": "4242"},
                    "credential": token_response,
                }
            ]
        }
        checkout = client.complete_checkout(
            checkout_id,
            payment=payment_data,
        )
        # Emit complete checkout event
        _emit_event(
            EventType.COMPLETE_CHECKOUT,
            "POST",
            f"/api/v1/checkout-sessions/{checkout_id}/complete",
            request_body={"payment": payment_data},
            response_body=checkout.model_dump(mode="json"),
        )

        # NOTE: Don't clear checkout ID - keep it so the "completed" state
        # is visible in the UI. The checkout will be cleared on session reset.

        return {
            UCP_CHECKOUT_KEY: checkout.model_dump(mode="json"),
            "status": "completed",
            "order": {
                "id": checkout.order.id if checkout.order else None,
                "url": checkout.order.permalink_url if checkout.order else None,
            },
            "total_charged": f"${checkout.totals.total / 100:.2f}" if checkout.totals else None,
        }

    except Exception:
        logging.exception("Error completing checkout")
        return _create_error_response("Could not complete checkout. Please try again.")


# ============================================================================
# CALLBACKS
# ============================================================================

# Track current tool call ID for matching results
_current_tool_call_id: str | None = None


def before_tool_callback(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
) -> dict | None:
    """Capture tool invocation before execution.

    Args:
        tool: The tool being called.
        args: The arguments passed to the tool.
        tool_context: The tool context.

    Returns:
        dict | None: Return dict to skip tool execution, None to proceed.
    """
    global _current_tool_call_id
    tool_name = tool.name if hasattr(tool, "name") else str(tool)

    # Capture the tool call event
    _current_tool_call_id = capture_agent_tool_call(
        tool_name=tool_name,
        args=args,
    )
    print(f"[AGENT] Tool call: {tool_name}({args})")

    # Return None to proceed with tool execution
    return None


def after_tool_modifier(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> dict | None:
    """Store UCP responses in state and capture tool result.

    Args:
        tool: The tool that was executed.
        args: The arguments passed to the tool.
        tool_context: The tool context.
        tool_response: The response from the tool.

    Returns:
        dict | None: Modified response or None to keep original.
    """
    global _current_tool_call_id

    tool_name = tool.name if hasattr(tool, "name") else str(tool)

    # Capture the tool result event
    if _current_tool_call_id:
        # Create a summary of the result for display
        result_summary = {}
        if "status" in tool_response:
            result_summary["status"] = tool_response["status"]
        if "message" in tool_response:
            result_summary["message"] = tool_response["message"]
        if "products" in tool_response:
            result_summary["products_count"] = len(tool_response.get("products", []))
        if "items" in tool_response:
            result_summary["items"] = tool_response["items"]
        if "totals" in tool_response:
            result_summary["totals"] = tool_response["totals"]
        if "new_total" in tool_response:
            result_summary["new_total"] = tool_response["new_total"]
        if "order" in tool_response:
            result_summary["order"] = tool_response["order"]

        capture_agent_tool_result(
            tool_call_id=_current_tool_call_id,
            tool_name=tool_name,
            result=result_summary if result_summary else {"raw": str(tool_response)[:200]},
            success=tool_response.get("status") != "error",
        )
        _current_tool_call_id = None

    # Store UCP responses in state
    ucp_response_keys = [UCP_CHECKOUT_KEY, UCP_PRODUCTS_KEY]

    if any(key in tool_response for key in ucp_response_keys):
        tool_context.state[ADK_LATEST_TOOL_RESULT] = tool_response

    return None


def modify_output_after_agent(callback_context: CallbackContext) -> types.Content | None:
    """Modify the agent's output before returning to the user.

    Adds UCP tool responses as structured output.

    Args:
        callback_context: The callback context for the agent run.

    Returns:
        types.Content | None: Modified agent output, or None.
    """
    latest_result = callback_context.state.get(ADK_LATEST_TOOL_RESULT)
    if latest_result:
        return types.Content(
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        response={"result": latest_result}
                    )
                )
            ],
            role="model",
        )
    return None


# ============================================================================
# AGENT DEFINITION
# ============================================================================


root_agent = Agent(
    name="cymbal_coffee_agent",
    model="gemini-3-flash-preview",
    description="AI shopping assistant for Cymbal Coffee Shop",
    instruction=(
        "You are a helpful shopping assistant for Cymbal Coffee Shop. "
        "You help customers browse products, add items to cart, apply discounts, "
        "select shipping, and complete orders.\n\n"
        "CRITICAL - SHIPPING SELECTION:\n"
        "When users say ANY of these after adding items to cart, they want to SELECT SHIPPING:\n"
        "- 'the first', 'the second', 'the third', '1st', '2nd', '3rd'\n"
        "- 'pickup', 'standard', 'express'\n"
        "- 'option 1', 'option 2', 'option 3'\n"
        "- Any number like '1', '2', '3'\n"
        "Map these to shipping option IDs:\n"
        "- 1st/first/pickup = 'pickup'\n"
        "- 2nd/second/standard = 'standard'\n"
        "- 3rd/third/express = 'express'\n"
        "Use select_shipping with the correct option_id. Do NOT add items or show menu!\n\n"
        "TOOL USAGE:\n"
        "1. show_menu - When users ask about products/menu\n"
        "2. add_to_cart - When users want to add specific items\n"
        "3. view_cart - When users want to see their cart\n"
        "4. select_shipping - When users choose delivery option (pickup/standard/express)\n"
        "5. apply_discount - When users mention promo codes\n"
        "6. complete_checkout - When users want to pay/checkout/complete order\n\n"
        "Be helpful and conversational. Use the tools to get current data."
    ),
    tools=[
        show_menu,
        add_to_cart,
        view_cart,
        select_shipping,
        apply_discount,
        complete_checkout,
    ],
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_modifier,
    after_agent_callback=modify_output_after_agent,
)


# ============================================================================
# SERVICE CLASS (Wrapper for API endpoints)
# ============================================================================


class ShoppingAgentService:
    """Service managing the ADK-based shopping agent.

    This class encapsulates the ADK Runner and session management,
    providing a clean interface for the chat endpoint.
    """

    def __init__(
        self,
        business_url: str = "http://localhost:8000",
        model_name: str = "gemini-3-flash-preview",
    ):
        """Initialize the shopping agent service.

        Args:
            business_url: URL of the UCP-compliant business
            model_name: Gemini model to use
        """
        global _ucp_client
        _ucp_client = UCPClient(business_url)

        self.business_url = business_url
        self.model_name = model_name
        self.ucp_client = _ucp_client

        # Session service for managing conversation state
        self._session_service = InMemorySessionService()

        # Check for API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not set, agent will use fallback mode")
            self._runner = None
        else:
            # Create the runner
            self._runner = Runner(
                agent=root_agent,
                app_name="cymbal_coffee_shop",
                session_service=self._session_service,
            )

        # Track products for formatting responses
        self._products: list[dict] = []
        self._discovered = False

    async def initialize(self) -> dict:
        """Initialize the agent by discovering the business."""
        self.ucp_client.discover()
        self._products = self.ucp_client.get_products()
        self._discovered = True

        return {
            "business": "discovered",
            "capabilities": self.ucp_client.get_capabilities(),
            "payment_handlers": self.ucp_client.get_payment_handlers(),
            "products_available": len(self._products),
        }

    async def chat_with_products(
        self,
        message: str,
        session_id: str = "default",
    ) -> tuple[str, list[dict] | None]:
        """Process a chat message and return response with optional products.

        Args:
            message: User's message
            session_id: Session ID for conversation continuity

        Returns:
            Tuple of (response text, products list or None)
        """
        if not self._discovered:
            await self.initialize()

        if not self._runner:
            # Fallback mode without API key
            return await self._fallback_chat(message)

        try:
            # Ensure session exists (create if not)
            session = await self._session_service.get_session(
                app_name="cymbal_coffee_shop",
                user_id="demo_user",
                session_id=session_id,
            )
            if session is None:
                session = await self._session_service.create_session(
                    app_name="cymbal_coffee_shop",
                    user_id="demo_user",
                    session_id=session_id,
                )

            # Collect final events from the agent run
            final_events: list = []

            async for event in self._runner.run_async(
                user_id="demo_user",
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=message)],
                ),
            ):
                # Collect events after first final response
                if event.is_final_response() or len(final_events) > 0:
                    final_events.append(event)

            # Process final events to extract text and data
            response_text = ""
            products = None
            data_found = False

            for final_event in final_events:
                if not hasattr(final_event, 'content') or not final_event.content:
                    continue

                for part in final_event.content.parts:
                    # Check for function_response with data
                    if hasattr(part, 'function_response') and part.function_response:
                        fr = part.function_response
                        if hasattr(fr, 'response') and fr.response:
                            result = fr.response.get('result', fr.response)
                            if isinstance(result, dict):
                                data_found = True
                                # Extract products if present
                                if UCP_PRODUCTS_KEY in result:
                                    products = result[UCP_PRODUCTS_KEY]

                    # Extract text content
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text

            # If we have a response, return it
            if response_text:
                return response_text, products

            # If no text but we processed data, return a default message
            if data_found:
                return "Here's the information you requested.", products

            return "I'm here to help! Try saying 'show menu' to see our products.", None

        except Exception as e:
            logger.exception("Error in agent chat")
            return await self._fallback_chat(message)

    async def _fallback_chat(self, message: str) -> tuple[str, list[dict] | None]:
        """Fallback chat when ADK is not available."""
        msg_lower = message.lower()

        # Simple keyword matching for demo
        if any(word in msg_lower for word in ["menu", "products", "browse", "show"]):
            if not self._products:
                await self.initialize()
            return "Here's our menu! Click on any item to add it to your cart.", self._products

        return """Hi! I'm your Cymbal Coffee Shop assistant. Here's what I can do:

- **Show menu** - See all our drinks and food
- **Add items** - "Add a latte to my cart"
- **Apply discounts** - "Use code DEMO20"
- **Select shipping** - "Pickup", "Standard", or "Express"
- **Checkout** - Complete your order

What would you like today?""", None

    async def chat(self, message: str, session_id: str = "default") -> str:
        """Process a chat message and return a response.

        Args:
            message: User's message
            session_id: Session ID for conversation continuity

        Returns:
            Agent's response
        """
        response, _ = await self.chat_with_products(message, session_id)
        return response

    async def get_checkout_id(self, session_id: str = "default") -> str | None:
        """Get the current checkout ID from the session state.

        Args:
            session_id: Session ID to look up

        Returns:
            The checkout ID if one exists, None otherwise
        """
        if not self._runner:
            return None

        try:
            session = await self._session_service.get_session(
                app_name="cymbal_coffee_shop",
                user_id="demo_user",
                session_id=session_id,
            )
            if session and session.state:
                return session.state.get(ADK_USER_CHECKOUT_ID)
        except Exception:
            pass
        return None


# Backwards compatibility alias
ShoppingAgent = ShoppingAgentService
