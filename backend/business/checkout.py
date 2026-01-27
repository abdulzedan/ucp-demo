"""Checkout capability handlers for UCP."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Header

from backend.business.catalog import (
    FULFILLMENT_OPTIONS,
    get_product,
    validate_discount_code,
)
from backend.schemas.checkout import (
    CheckoutSession,
    CheckoutStatus,
    CompleteCheckoutRequest,
    CreateCheckoutRequest,
    Discount,
    Fulfillment,
    FulfillmentOption,
    LineItem,
    Link,
    Message,
    MessageSeverity,
    MessageType,
    OrderConfirmation,
    Total,
    UpdateCheckoutRequest,
)
from backend.schemas.ucp import UCPResponseMetadata

router = APIRouter(prefix="/api/v1")

# In-memory storage for checkout sessions (demo purposes)
checkout_sessions: dict[str, dict] = {}


def get_ucp_metadata() -> UCPResponseMetadata:
    """Get UCP metadata for responses."""
    return UCPResponseMetadata(
        version="2026-01-11",
        capabilities={
            "dev.ucp.shopping.checkout": [{"version": "2026-01-11"}],
            "dev.ucp.shopping.fulfillment": [{"version": "2026-01-11"}],
            "dev.ucp.shopping.discount": [{"version": "2026-01-11"}],
        },
        payment_handlers={
            "dev.ucp.demo.mock_tokenizer": [
                {"id": "mock_tokenizer_001", "version": "2026-01-11"}
            ]
        },
    )


def calculate_totals(
    line_items: list[LineItem],
    discounts: list[Discount],
    fulfillment: Fulfillment | None,
) -> Total:
    """Calculate checkout totals."""
    subtotal = sum(item.total_price for item in line_items)

    # Calculate discount
    discount_amount = sum(d.amount for d in discounts)

    # Calculate shipping
    shipping = 0
    if fulfillment and fulfillment.selected_option_id:
        for opt in FULFILLMENT_OPTIONS:
            if opt["id"] == fulfillment.selected_option_id:
                # Check for free shipping discount
                has_free_shipping = any(
                    d.code.upper() == "FREESHIP" for d in discounts
                )
                if not has_free_shipping:
                    shipping = opt["price"]
                break

    # Calculate tax (demo: 8% on subtotal after discount)
    taxable = max(0, subtotal - discount_amount)
    tax = int(taxable * 0.08)

    total = subtotal - discount_amount + shipping + tax

    return Total(
        subtotal=subtotal,
        discount=discount_amount,
        shipping=shipping,
        tax=tax,
        total=max(0, total),
        currency="USD",
    )


def determine_status(
    line_items: list[LineItem],
    fulfillment: Fulfillment | None,
    messages: list[Message],
) -> CheckoutStatus:
    """Determine checkout status based on current state."""
    # Check for escalation-level errors
    has_escalation = any(
        m.type == MessageType.ERROR
        and m.severity
        in [MessageSeverity.REQUIRES_BUYER_INPUT, MessageSeverity.REQUIRES_BUYER_REVIEW]
        for m in messages
    )
    if has_escalation:
        return CheckoutStatus.REQUIRES_ESCALATION

    # Check for recoverable errors
    has_errors = any(
        m.type == MessageType.ERROR and m.severity == MessageSeverity.RECOVERABLE
        for m in messages
    )
    if has_errors:
        return CheckoutStatus.INCOMPLETE

    # Check if we have minimum required info
    if not line_items:
        return CheckoutStatus.INCOMPLETE

    # Check if fulfillment is configured (if items require shipping)
    if fulfillment is None:
        return CheckoutStatus.INCOMPLETE

    if fulfillment.selected_option_id is None:
        return CheckoutStatus.INCOMPLETE

    # Check if shipping address is provided for delivery options
    if fulfillment.selected_option_id in ["standard", "express"]:
        if fulfillment.address is None:
            return CheckoutStatus.INCOMPLETE

    return CheckoutStatus.READY_FOR_COMPLETE


def build_messages(
    line_items: list[LineItem],
    fulfillment: Fulfillment | None,
) -> list[Message]:
    """Build messages based on checkout state."""
    messages = []

    if not line_items:
        messages.append(
            Message(
                type=MessageType.WARNING,
                code="empty_cart",
                content="Your cart is empty. Add some items to continue.",
            )
        )

    if fulfillment is None:
        messages.append(
            Message(
                type=MessageType.INFO,
                code="select_fulfillment",
                content="Please select a fulfillment option.",
            )
        )
    elif fulfillment.selected_option_id is None:
        messages.append(
            Message(
                type=MessageType.ERROR,
                code="fulfillment_required",
                content="Please select a fulfillment option to continue.",
                severity=MessageSeverity.RECOVERABLE,
            )
        )
    elif fulfillment.selected_option_id in ["standard", "express"]:
        if fulfillment.address is None:
            messages.append(
                Message(
                    type=MessageType.ERROR,
                    code="address_required",
                    content="Please provide a delivery address.",
                    severity=MessageSeverity.RECOVERABLE,
                )
            )

    return messages


def build_checkout_response(session_data: dict) -> CheckoutSession:
    """Build a CheckoutSession response from stored data."""
    line_items = session_data.get("line_items", [])
    discounts = session_data.get("discounts", [])
    fulfillment = session_data.get("fulfillment")

    messages = build_messages(line_items, fulfillment)
    status = session_data.get("status")

    # If not completed/canceled, recalculate status
    if status not in [CheckoutStatus.COMPLETED, CheckoutStatus.CANCELED]:
        status = determine_status(line_items, fulfillment, messages)

    totals = calculate_totals(line_items, discounts, fulfillment)

    return CheckoutSession(
        ucp=get_ucp_metadata(),
        id=session_data["id"],
        status=status,
        line_items=line_items,
        buyer=session_data.get("buyer"),
        fulfillment=fulfillment,
        discounts=discounts,
        totals=totals,
        messages=messages,
        links=[
            Link(
                type="privacy_policy",
                href="https://example.com/privacy",
                title="Privacy Policy",
            ),
            Link(
                type="terms_of_service",
                href="https://example.com/terms",
                title="Terms of Service",
            ),
        ],
        continue_url=f"http://localhost:8000/checkout/{session_data['id']}",
        expires_at=session_data.get("expires_at"),
        order=session_data.get("order"),
        created_at=session_data["created_at"],
        updated_at=session_data["updated_at"],
    )


@router.post("/checkout-sessions", response_model=CheckoutSession)
async def create_checkout(
    request: CreateCheckoutRequest,
    ucp_agent: str | None = Header(default=None, alias="UCP-Agent"),
) -> CheckoutSession:
    """Create a new checkout session.

    This initiates a checkout session with the provided items.
    The platform should call this when a user expresses purchase intent.
    """
    session_id = f"cs_{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc)

    # Process line items
    line_items: list[LineItem] = []
    for i, item_req in enumerate(request.line_items):
        product = get_product(item_req.product_id)
        if product is None:
            raise HTTPException(
                status_code=400,
                detail=f"Product not found: {item_req.product_id}",
            )

        line_items.append(
            LineItem(
                id=f"li_{uuid.uuid4().hex[:8]}",
                product_id=product.id,
                title=product.title,
                description=product.description,
                image_url=product.image_url,
                quantity=item_req.quantity,
                unit_price=product.price,
                total_price=product.price * item_req.quantity,
                currency=product.currency,
            )
        )

    # Process discount codes
    discounts: list[Discount] = []
    for code in request.discount_codes:
        discount_info = validate_discount_code(code)
        if discount_info:
            # Calculate discount amount
            subtotal = sum(item.total_price for item in line_items)
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

    # Build fulfillment with available options
    fulfillment = Fulfillment(
        type="shipping",
        address=request.fulfillment.address if request.fulfillment else None,
        selected_option_id=(
            request.fulfillment.selected_option_id if request.fulfillment else None
        ),
        available_options=[
            FulfillmentOption(**opt) for opt in FULFILLMENT_OPTIONS
        ],
    )

    # Store session
    session_data = {
        "id": session_id,
        "line_items": line_items,
        "buyer": request.buyer,
        "fulfillment": fulfillment,
        "discounts": discounts,
        "status": None,  # Will be calculated
        "order": None,
        "created_at": now,
        "updated_at": now,
        "expires_at": now + timedelta(hours=24),
    }
    checkout_sessions[session_id] = session_data

    return build_checkout_response(session_data)


@router.get("/checkout-sessions/{session_id}", response_model=CheckoutSession)
async def get_checkout(session_id: str) -> CheckoutSession:
    """Get the current state of a checkout session."""
    if session_id not in checkout_sessions:
        raise HTTPException(status_code=404, detail="Checkout session not found")

    return build_checkout_response(checkout_sessions[session_id])


@router.put("/checkout-sessions/{session_id}", response_model=CheckoutSession)
async def update_checkout(
    session_id: str,
    request: UpdateCheckoutRequest,
) -> CheckoutSession:
    """Update an existing checkout session.

    This performs a full replacement of the checkout session state.
    The platform must send the complete state including any updates.
    """
    if session_id not in checkout_sessions:
        raise HTTPException(status_code=404, detail="Checkout session not found")

    session_data = checkout_sessions[session_id]

    # Check if session can be updated
    if session_data.get("status") in [
        CheckoutStatus.COMPLETED,
        CheckoutStatus.CANCELED,
    ]:
        raise HTTPException(
            status_code=400,
            detail="Cannot update a completed or canceled checkout session",
        )

    now = datetime.now(timezone.utc)

    # Process line items
    line_items: list[LineItem] = []
    for item_req in request.line_items:
        product = get_product(item_req.product_id)
        if product is None:
            raise HTTPException(
                status_code=400,
                detail=f"Product not found: {item_req.product_id}",
            )

        line_items.append(
            LineItem(
                id=f"li_{uuid.uuid4().hex[:8]}",
                product_id=product.id,
                title=product.title,
                description=product.description,
                image_url=product.image_url,
                quantity=item_req.quantity,
                unit_price=product.price,
                total_price=product.price * item_req.quantity,
                currency=product.currency,
            )
        )

    # Process discount codes
    discounts: list[Discount] = []
    for code in request.discount_codes:
        discount_info = validate_discount_code(code)
        if discount_info:
            subtotal = sum(item.total_price for item in line_items)
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
    fulfillment = None
    if request.fulfillment:
        fulfillment = Fulfillment(
            type="shipping",
            address=request.fulfillment.address,
            selected_option_id=request.fulfillment.selected_option_id,
            available_options=[
                FulfillmentOption(**opt) for opt in FULFILLMENT_OPTIONS
            ],
        )

    # Update session
    session_data.update(
        {
            "line_items": line_items,
            "buyer": request.buyer,
            "fulfillment": fulfillment,
            "discounts": discounts,
            "updated_at": now,
        }
    )

    return build_checkout_response(session_data)


@router.post("/checkout-sessions/{session_id}/complete", response_model=CheckoutSession)
async def complete_checkout(
    session_id: str,
    request: CompleteCheckoutRequest,
) -> CheckoutSession:
    """Complete the checkout and place the order.

    This finalizes the checkout session. The payment information
    should include instruments acquired from the payment handler.
    """
    if session_id not in checkout_sessions:
        raise HTTPException(status_code=404, detail="Checkout session not found")

    session_data = checkout_sessions[session_id]

    # Check if session can be completed
    if session_data.get("status") == CheckoutStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Checkout session is already completed",
        )

    if session_data.get("status") == CheckoutStatus.CANCELED:
        raise HTTPException(
            status_code=400,
            detail="Cannot complete a canceled checkout session",
        )

    # Validate payment (demo: just check that we have payment info)
    if request.payment is None:
        raise HTTPException(
            status_code=400,
            detail="Payment information is required",
        )

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


@router.post("/checkout-sessions/{session_id}/cancel", response_model=CheckoutSession)
async def cancel_checkout(session_id: str) -> CheckoutSession:
    """Cancel a checkout session."""
    if session_id not in checkout_sessions:
        raise HTTPException(status_code=404, detail="Checkout session not found")

    session_data = checkout_sessions[session_id]

    # Check if session can be canceled
    if session_data.get("status") == CheckoutStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a completed checkout session",
        )

    if session_data.get("status") == CheckoutStatus.CANCELED:
        raise HTTPException(
            status_code=400,
            detail="Checkout session is already canceled",
        )

    now = datetime.now(timezone.utc)

    # Update session
    session_data.update(
        {
            "status": CheckoutStatus.CANCELED,
            "updated_at": now,
        }
    )

    return build_checkout_response(session_data)


@router.get("/products")
async def list_products() -> list[dict]:
    """List all available products.

    This is a convenience endpoint for the demo, not part of UCP spec.
    """
    from backend.business.catalog import get_all_products

    products = get_all_products()
    return [p.model_dump() for p in products]


@router.post("/tokenize")
async def mock_tokenize(request: dict[str, Any]) -> dict:
    """Mock payment tokenization endpoint.

    This simulates a payment provider's tokenization service.
    In production, this would be handled by a real PSP.
    """
    return {
        "token": f"tok_{uuid.uuid4().hex[:16]}",
        "type": "TOKEN",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
    }
