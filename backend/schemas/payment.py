"""Payment schemas for UCP checkout."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PaymentInstrumentType(str, Enum):
    """Types of payment instruments."""

    CARD = "card"
    BANK_ACCOUNT = "bank_account"
    DIGITAL_WALLET = "digital_wallet"


class PaymentCredentialType(str, Enum):
    """Types of payment credentials."""

    PAYMENT_GATEWAY = "PAYMENT_GATEWAY"
    DIRECT = "DIRECT"
    TOKEN = "TOKEN"


class PaymentCredential(BaseModel):
    """Payment credential returned by payment handler."""

    type: PaymentCredentialType = Field(description="Credential type")
    token: str = Field(description="Payment token or encrypted data")


class PaymentDisplay(BaseModel):
    """Display information for payment instrument."""

    brand: str | None = Field(default=None, description="Card brand (visa, mastercard)")
    last_digits: str | None = Field(default=None, description="Last 4 digits")


class PaymentInstrument(BaseModel):
    """Payment instrument for checkout completion."""

    id: str = Field(description="Instrument ID")
    handler_id: str = Field(description="Payment handler ID that processed this")
    type: PaymentInstrumentType = Field(description="Instrument type")
    selected: bool = Field(default=True, description="Whether this is selected")
    display: PaymentDisplay | None = Field(
        default=None, description="Display information"
    )
    billing_address: dict[str, Any] | None = Field(
        default=None, description="Billing address"
    )
    credential: PaymentCredential = Field(description="Payment credential")


class Payment(BaseModel):
    """Payment information in complete checkout request."""

    instruments: list[PaymentInstrument] = Field(
        default_factory=list, description="Payment instruments"
    )
