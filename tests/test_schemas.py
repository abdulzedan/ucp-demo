"""Tests for Pydantic schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from backend.schemas.checkout import (
    CheckoutStatus,
    MessageType,
    MessageSeverity,
    PostalAddress,
    Buyer,
    Item,
    LineItemRequest,
    LineItem,
    FulfillmentOption,
    Fulfillment,
    Discount,
    Total,
    Message,
)


class TestCheckoutStatus:
    """Tests for CheckoutStatus enum."""

    def test_all_statuses_defined(self):
        """All expected statuses should be defined."""
        expected = [
            "incomplete",
            "requires_escalation",
            "ready_for_complete",
            "complete_in_progress",
            "completed",
            "canceled",
        ]
        actual = [s.value for s in CheckoutStatus]
        assert set(expected) == set(actual)


class TestPostalAddress:
    """Tests for PostalAddress schema."""

    def test_empty_address_valid(self):
        """Empty address should be valid (all fields optional)."""
        address = PostalAddress()
        assert address.street_address is None

    def test_full_address(self):
        """Full address should parse correctly."""
        address = PostalAddress(
            street_address="123 Main St",
            address_locality="San Francisco",
            address_region="CA",
            postal_code="94102",
            address_country="US",
        )
        assert address.street_address == "123 Main St"
        assert address.address_locality == "San Francisco"


class TestItem:
    """Tests for Item schema."""

    def test_valid_item(self):
        """Valid item should parse correctly."""
        item = Item(
            id="test_item",
            title="Test Item",
            price=999,
        )
        assert item.id == "test_item"
        assert item.price == 999
        assert item.currency == "USD"  # default

    def test_item_requires_id(self):
        """Item should require id."""
        with pytest.raises(ValidationError):
            Item(title="Test", price=100)

    def test_item_requires_title(self):
        """Item should require title."""
        with pytest.raises(ValidationError):
            Item(id="test", price=100)

    def test_item_requires_price(self):
        """Item should require price."""
        with pytest.raises(ValidationError):
            Item(id="test", title="Test")


class TestLineItemRequest:
    """Tests for LineItemRequest schema."""

    def test_valid_line_item_request(self):
        """Valid request should parse correctly."""
        request = LineItemRequest(product_id="latte_medium", quantity=2)
        assert request.product_id == "latte_medium"
        assert request.quantity == 2

    def test_default_quantity(self):
        """Default quantity should be 1."""
        request = LineItemRequest(product_id="latte_medium")
        assert request.quantity == 1

    def test_quantity_must_be_positive(self):
        """Quantity must be >= 1."""
        with pytest.raises(ValidationError):
            LineItemRequest(product_id="test", quantity=0)
        with pytest.raises(ValidationError):
            LineItemRequest(product_id="test", quantity=-1)


class TestTotal:
    """Tests for Total schema."""

    def test_valid_total(self):
        """Valid total should parse correctly."""
        total = Total(
            subtotal=1000,
            discount=100,
            shipping=500,
            tax=80,
            total=1480,
        )
        assert total.subtotal == 1000
        assert total.total == 1480

    def test_default_values(self):
        """Default values should be 0 for optional fields."""
        total = Total(subtotal=1000, total=1000)
        assert total.discount == 0
        assert total.shipping == 0
        assert total.tax == 0


class TestMessage:
    """Tests for Message schema."""

    def test_error_message(self):
        """Error message should parse correctly."""
        msg = Message(
            type=MessageType.ERROR,
            code="missing_field",
            content="Email is required",
            severity=MessageSeverity.RECOVERABLE,
        )
        assert msg.type == MessageType.ERROR
        assert msg.severity == MessageSeverity.RECOVERABLE

    def test_info_message_no_severity(self):
        """Info message doesn't need severity."""
        msg = Message(
            type=MessageType.INFO,
            code="promo_available",
            content="Use DEMO20 for 20% off!",
        )
        assert msg.type == MessageType.INFO
        assert msg.severity is None


class TestDiscount:
    """Tests for Discount schema."""

    def test_valid_discount(self):
        """Valid discount should parse correctly."""
        discount = Discount(
            code="DEMO20",
            title="Demo Discount",
            amount=500,
        )
        assert discount.code == "DEMO20"
        assert discount.amount == 500
        assert discount.currency == "USD"
