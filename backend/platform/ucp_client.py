"""UCP Client - Direct function calls to business logic (no HTTP to self).

This client calls the business logic directly instead of making HTTP requests,
avoiding the self-calling deadlock when running in a single server process.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.business.catalog import (
    FULFILLMENT_OPTIONS,
    get_all_products,
    get_product,
    validate_discount_code,
)
from backend.business.checkout import (
    build_checkout_response,
    checkout_sessions,
)
from backend.schemas.checkout import (
    Buyer,
    CheckoutSession,
    CheckoutStatus,
    Discount,
    Fulfillment,
    FulfillmentOption,
    LineItem,
    OrderConfirmation,
    PostalAddress,
)
from backend.schemas.ucp import UCPProfile


class UCPClient:
    """Client for UCP operations using direct function calls.

    This avoids HTTP self-calling deadlock by directly invoking
    the business logic functions.
    """

    def __init__(
        self,
        business_url: str,
        platform_profile_url: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the UCP client.

        Args:
            business_url: Base URL of the business server (for reference only)
            platform_profile_url: URL to this platform's UCP profile
            timeout: Request timeout in seconds (unused in direct mode)
        """
        self.business_url = business_url.rstrip("/")
        self.platform_profile_url = platform_profile_url
        self._profile: UCPProfile | None = None
        self._discovered = False

    def discover(self) -> UCPProfile:
        """Discover business capabilities.

        Returns a pre-built UCP profile since we're running in the same process.
        """
        # Build profile directly from known capabilities
        self._profile = UCPProfile(
            ucp={
                "version": "2026-01-11",
                "capabilities": {
                    "dev.ucp.shopping.checkout": [
                        {
                            "version": "2026-01-11",
                            "spec": "https://ucp.dev/specification/checkout",
                            "schema": "https://ucp.dev/schemas/shopping/checkout.json",
                        }
                    ],
                    "dev.ucp.shopping.fulfillment": [
                        {
                            "version": "2026-01-11",
                            "spec": "https://ucp.dev/specification/fulfillment",
                            "schema": "https://ucp.dev/schemas/shopping/fulfillment.json",
                            "extends": "dev.ucp.shopping.checkout",
                        }
                    ],
                    "dev.ucp.shopping.discount": [
                        {
                            "version": "2026-01-11",
                            "spec": "https://ucp.dev/specification/discount",
                            "schema": "https://ucp.dev/schemas/shopping/discount.json",
                            "extends": "dev.ucp.shopping.checkout",
                        }
                    ],
                },
                "payment_handlers": {
                    "dev.ucp.demo.mock_tokenizer": [
                        {"id": "mock_tokenizer_001", "version": "2026-01-11"}
                    ]
                },
                "services": {},
            }
        )
        self._discovered = True
        return self._profile

    @property
    def profile(self) -> UCPProfile | None:
        return self._profile

    @property
    def api_endpoint(self) -> str:
        return f"{self.business_url}/api/v1"

    def get_capabilities(self) -> list[str]:
        if not self._profile:
            return []
        return list(self._profile.ucp.capabilities.keys())

    def get_payment_handlers(self) -> list[dict]:
        if not self._profile:
            return []
        handlers = []
        for name, handler_list in self._profile.ucp.payment_handlers.items():
            for handler in handler_list:
                handlers.append(
                    {
                        "name": name,
                        "id": handler.id,
                        "version": handler.version,
                        "config": handler.config,
                    }
                )
        return handlers

    def get_products(self) -> list[dict]:
        """Get available products directly from catalog."""
        products = get_all_products()
        return [p.model_dump() for p in products]

    def create_checkout(
        self,
        line_items: list[dict[str, Any]],
        buyer: dict[str, Any] | None = None,
        fulfillment: dict[str, Any] | None = None,
        discount_codes: list[str] | None = None,
    ) -> CheckoutSession:
        """Create a new checkout session."""
        session_id = f"cs_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        # Process line items
        processed_items: list[LineItem] = []
        for item in line_items:
            product = get_product(item["product_id"])
            if product is None:
                raise ValueError(f"Product not found: {item['product_id']}")

            qty = item.get("quantity", 1)
            processed_items.append(
                LineItem(
                    id=f"li_{uuid.uuid4().hex[:8]}",
                    product_id=product.id,
                    title=product.title,
                    description=product.description,
                    image_url=product.image_url,
                    quantity=qty,
                    unit_price=product.price,
                    total_price=product.price * qty,
                    currency=product.currency,
                )
            )

        # Process discounts
        discounts: list[Discount] = []
        for code in discount_codes or []:
            discount_info = validate_discount_code(code)
            if discount_info:
                subtotal = sum(item.total_price for item in processed_items)
                if discount_info["type"] == "percentage":
                    amount = int(subtotal * discount_info["value"] / 100)
                elif discount_info["type"] == "fixed":
                    amount = min(discount_info["value"], subtotal)
                else:
                    amount = 0
                discounts.append(
                    Discount(
                        code=code.upper(),
                        title=discount_info["title"],
                        amount=amount,
                        currency="USD",
                    )
                )

        # Build fulfillment
        fulfillment_obj = Fulfillment(
            type="shipping",
            address=PostalAddress(**fulfillment["address"])
            if fulfillment and fulfillment.get("address")
            else None,
            selected_option_id=fulfillment.get("selected_option_id")
            if fulfillment
            else None,
            available_options=[FulfillmentOption(**opt) for opt in FULFILLMENT_OPTIONS],
        )

        # Store session
        session_data = {
            "id": session_id,
            "line_items": processed_items,
            "buyer": Buyer(**buyer) if buyer else None,
            "fulfillment": fulfillment_obj,
            "discounts": discounts,
            "status": None,
            "order": None,
            "created_at": now,
            "updated_at": now,
            "expires_at": now + timedelta(hours=24),
        }
        checkout_sessions[session_id] = session_data

        return build_checkout_response(session_data)

    def get_checkout(self, session_id: str) -> CheckoutSession:
        """Get checkout session."""
        if session_id not in checkout_sessions:
            raise ValueError(f"Checkout session not found: {session_id}")
        return build_checkout_response(checkout_sessions[session_id])

    def update_checkout(
        self,
        session_id: str,
        line_items: list[dict[str, Any]] | None = None,
        buyer: dict[str, Any] | None = None,
        fulfillment: dict[str, Any] | None = None,
        discount_codes: list[str] | None = None,
    ) -> CheckoutSession:
        """Update checkout session."""
        if session_id not in checkout_sessions:
            raise ValueError(f"Checkout session not found: {session_id}")

        session_data = checkout_sessions[session_id]
        now = datetime.now(timezone.utc)

        # Process line items
        processed_items: list[LineItem] = []
        for item in line_items or []:
            product = get_product(item["product_id"])
            if product is None:
                raise ValueError(f"Product not found: {item['product_id']}")

            qty = item.get("quantity", 1)
            processed_items.append(
                LineItem(
                    id=f"li_{uuid.uuid4().hex[:8]}",
                    product_id=product.id,
                    title=product.title,
                    description=product.description,
                    image_url=product.image_url,
                    quantity=qty,
                    unit_price=product.price,
                    total_price=product.price * qty,
                    currency=product.currency,
                )
            )

        # Process discounts
        discounts: list[Discount] = []
        for code in discount_codes or []:
            discount_info = validate_discount_code(code)
            if discount_info:
                subtotal = sum(item.total_price for item in processed_items)
                if discount_info["type"] == "percentage":
                    amount = int(subtotal * discount_info["value"] / 100)
                elif discount_info["type"] == "fixed":
                    amount = min(discount_info["value"], subtotal)
                else:
                    amount = 0
                discounts.append(
                    Discount(
                        code=code.upper(),
                        title=discount_info["title"],
                        amount=amount,
                        currency="USD",
                    )
                )

        # Build fulfillment
        fulfillment_obj = None
        if fulfillment:
            fulfillment_obj = Fulfillment(
                type="shipping",
                address=PostalAddress(**fulfillment["address"])
                if fulfillment.get("address")
                else None,
                selected_option_id=fulfillment.get("selected_option_id"),
                available_options=[
                    FulfillmentOption(**opt) for opt in FULFILLMENT_OPTIONS
                ],
            )

        # Update session
        session_data.update(
            {
                "line_items": processed_items,
                "buyer": Buyer(**buyer) if buyer else None,
                "fulfillment": fulfillment_obj,
                "discounts": discounts,
                "updated_at": now,
            }
        )

        return build_checkout_response(session_data)

    def complete_checkout(
        self,
        session_id: str,
        payment: dict[str, Any],
        risk_signals: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        """Complete checkout and create order."""
        if session_id not in checkout_sessions:
            raise ValueError(f"Checkout session not found: {session_id}")

        session_data = checkout_sessions[session_id]
        now = datetime.now(timezone.utc)

        # Create order
        order = OrderConfirmation(
            id=f"ord_{uuid.uuid4().hex[:12]}",
            permalink_url=f"http://localhost:8000/orders/ord_{uuid.uuid4().hex[:12]}",
            created_at=now,
        )

        # Update session
        session_data.update(
            {
                "status": CheckoutStatus.COMPLETED,
                "order": order,
                "updated_at": now,
            }
        )

        return build_checkout_response(session_data)

    def cancel_checkout(self, session_id: str) -> CheckoutSession:
        """Cancel checkout session."""
        if session_id not in checkout_sessions:
            raise ValueError(f"Checkout session not found: {session_id}")

        session_data = checkout_sessions[session_id]
        now = datetime.now(timezone.utc)

        session_data.update(
            {
                "status": CheckoutStatus.CANCELED,
                "updated_at": now,
            }
        )

        return build_checkout_response(session_data)

    def tokenize_payment(
        self,
        handler_id: str,
        card_details: dict[str, Any],
    ) -> dict:
        """Mock payment tokenization."""
        return {
            "token": f"tok_{uuid.uuid4().hex[:16]}",
            "type": "TOKEN",
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=15)
            ).isoformat(),
        }

    # Async wrappers for backwards compatibility
    async def discover_async(self) -> UCPProfile:
        return self.discover()

    async def get_products_async(self) -> list[dict]:
        return self.get_products()
