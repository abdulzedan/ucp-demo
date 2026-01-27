"""Checkout capability schemas based on UCP specification."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.schemas.ucp import UCPResponseMetadata


class CheckoutStatus(str, Enum):
    """Checkout session status values."""

    INCOMPLETE = "incomplete"
    REQUIRES_ESCALATION = "requires_escalation"
    READY_FOR_COMPLETE = "ready_for_complete"
    COMPLETE_IN_PROGRESS = "complete_in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class MessageType(str, Enum):
    """Message types in checkout responses."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class MessageSeverity(str, Enum):
    """Error severity levels."""

    RECOVERABLE = "recoverable"
    REQUIRES_BUYER_INPUT = "requires_buyer_input"
    REQUIRES_BUYER_REVIEW = "requires_buyer_review"


class PostalAddress(BaseModel):
    """Postal address for shipping/billing."""

    street_address: str | None = Field(default=None, description="Street address")
    extended_address: str | None = Field(
        default=None, description="Extended address (apt, suite)"
    )
    address_locality: str | None = Field(default=None, description="City")
    address_region: str | None = Field(default=None, description="State/province")
    postal_code: str | None = Field(default=None, description="Postal/ZIP code")
    address_country: str | None = Field(
        default=None, description="Country code (ISO 3166-1 alpha-2)"
    )
    first_name: str | None = Field(default=None, description="First name")
    last_name: str | None = Field(default=None, description="Last name")


class Buyer(BaseModel):
    """Buyer information for checkout."""

    email: str | None = Field(default=None, description="Buyer email")
    phone: str | None = Field(default=None, description="Buyer phone number")
    first_name: str | None = Field(default=None, description="First name")
    last_name: str | None = Field(default=None, description="Last name")
    billing_address: PostalAddress | None = Field(
        default=None, description="Billing address"
    )


class Item(BaseModel):
    """Product item in the catalog."""

    id: str = Field(description="Product identifier")
    title: str = Field(description="Product title")
    description: str | None = Field(default=None, description="Product description")
    image_url: str | None = Field(default=None, description="Product image URL")
    price: int = Field(description="Price in minor units (cents)")
    currency: str = Field(default="USD", description="Currency code")


class LineItemRequest(BaseModel):
    """Line item in create/update checkout request."""

    product_id: str = Field(description="Product identifier")
    quantity: int = Field(default=1, ge=1, description="Quantity")


class LineItem(BaseModel):
    """Line item in checkout response."""

    id: str = Field(description="Line item ID")
    product_id: str = Field(description="Product identifier")
    title: str = Field(description="Product title")
    description: str | None = Field(default=None, description="Product description")
    image_url: str | None = Field(default=None, description="Product image URL")
    quantity: int = Field(ge=1, description="Quantity")
    unit_price: int = Field(description="Unit price in minor units")
    total_price: int = Field(description="Total price (unit_price * quantity)")
    currency: str = Field(default="USD", description="Currency code")


class FulfillmentOption(BaseModel):
    """Shipping/fulfillment option."""

    id: str = Field(description="Option identifier")
    title: str = Field(description="Option title (e.g., 'Standard Shipping')")
    description: str | None = Field(default=None, description="Option description")
    price: int = Field(description="Shipping price in minor units")
    currency: str = Field(default="USD", description="Currency code")
    estimated_delivery: str | None = Field(
        default=None, description="Estimated delivery timeframe"
    )


class Fulfillment(BaseModel):
    """Fulfillment details for checkout."""

    type: str = Field(default="shipping", description="Fulfillment type")
    address: PostalAddress | None = Field(default=None, description="Shipping address")
    selected_option_id: str | None = Field(
        default=None, description="Selected fulfillment option ID"
    )
    available_options: list[FulfillmentOption] = Field(
        default_factory=list, description="Available fulfillment options"
    )


class Discount(BaseModel):
    """Applied discount."""

    code: str = Field(description="Discount code")
    title: str = Field(description="Discount title")
    amount: int = Field(description="Discount amount in minor units")
    currency: str = Field(default="USD", description="Currency code")


class Total(BaseModel):
    """Checkout totals."""

    subtotal: int = Field(description="Subtotal before discounts and shipping")
    discount: int = Field(default=0, description="Total discount amount")
    shipping: int = Field(default=0, description="Shipping cost")
    tax: int = Field(default=0, description="Tax amount")
    total: int = Field(description="Final total")
    currency: str = Field(default="USD", description="Currency code")


class Message(BaseModel):
    """Message in checkout response (error, warning, info)."""

    type: MessageType = Field(description="Message type")
    code: str = Field(description="Message code for programmatic handling")
    content: str = Field(description="Human-readable message")
    severity: MessageSeverity | None = Field(
        default=None, description="Severity (for errors)"
    )


class Link(BaseModel):
    """Link to business policies or resources."""

    type: str = Field(description="Link type (e.g., 'privacy_policy')")
    href: str = Field(description="Link URL")
    title: str | None = Field(default=None, description="Link title")


class OrderConfirmation(BaseModel):
    """Order confirmation details after checkout completion."""

    id: str = Field(description="Order ID")
    permalink_url: str | None = Field(default=None, description="Order status page URL")
    created_at: datetime = Field(description="Order creation timestamp")


class CheckoutSessionBase(BaseModel):
    """Base checkout session fields."""

    line_items: list[LineItemRequest] = Field(
        default_factory=list, description="Items in checkout"
    )
    buyer: Buyer | None = Field(default=None, description="Buyer information")
    fulfillment: Fulfillment | None = Field(
        default=None, description="Fulfillment details"
    )
    discount_codes: list[str] = Field(
        default_factory=list, description="Applied discount codes"
    )


class CreateCheckoutRequest(CheckoutSessionBase):
    """Request to create a new checkout session."""

    context: dict[str, Any] | None = Field(
        default=None, description="Context signals (locale, currency, etc.)"
    )


class UpdateCheckoutRequest(CheckoutSessionBase):
    """Request to update an existing checkout session."""

    pass


class CompleteCheckoutRequest(BaseModel):
    """Request to complete a checkout session."""

    payment: dict[str, Any] | None = Field(
        default=None, description="Payment information"
    )
    risk_signals: dict[str, Any] | None = Field(
        default=None, description="Risk assessment signals"
    )


class CheckoutSession(BaseModel):
    """Full checkout session response."""

    ucp: UCPResponseMetadata = Field(description="UCP metadata")
    id: str = Field(description="Checkout session ID")
    status: CheckoutStatus = Field(description="Current checkout status")
    line_items: list[LineItem] = Field(
        default_factory=list, description="Items in checkout"
    )
    buyer: Buyer | None = Field(default=None, description="Buyer information")
    fulfillment: Fulfillment | None = Field(
        default=None, description="Fulfillment details"
    )
    discounts: list[Discount] = Field(
        default_factory=list, description="Applied discounts"
    )
    totals: Total | None = Field(default=None, description="Checkout totals")
    messages: list[Message] = Field(
        default_factory=list, description="Messages (errors, warnings, info)"
    )
    links: list[Link] = Field(
        default_factory=list, description="Business policy links"
    )
    continue_url: str | None = Field(
        default=None, description="URL for buyer handoff"
    )
    expires_at: datetime | None = Field(
        default=None, description="Session expiration timestamp"
    )
    order: OrderConfirmation | None = Field(
        default=None, description="Order details (after completion)"
    )
    created_at: datetime = Field(description="Session creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
