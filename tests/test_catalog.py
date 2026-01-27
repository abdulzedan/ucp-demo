"""Tests for the product catalog."""

import pytest

from backend.business.catalog import (
    CATALOG,
    DISCOUNT_CODES,
    FULFILLMENT_OPTIONS,
    get_product,
    get_all_products,
    validate_discount_code,
    get_fulfillment_options,
)


class TestCatalog:
    """Tests for catalog functions."""

    def test_catalog_not_empty(self):
        """Catalog should have products."""
        assert len(CATALOG) > 0

    def test_get_product_exists(self):
        """Should return product when it exists."""
        product = get_product("latte_medium")
        assert product is not None
        assert product.id == "latte_medium"
        assert product.title == "Medium Latte"
        assert product.price == 549

    def test_get_product_not_exists(self):
        """Should return None for non-existent product."""
        product = get_product("nonexistent_product")
        assert product is None

    def test_get_all_products(self):
        """Should return all products."""
        products = get_all_products()
        assert len(products) == len(CATALOG)
        assert all(hasattr(p, "id") for p in products)
        assert all(hasattr(p, "price") for p in products)

    def test_product_has_required_fields(self):
        """All products should have required fields."""
        for product_id, product in CATALOG.items():
            assert product.id == product_id
            assert product.title
            assert product.price > 0
            assert product.currency == "USD"


class TestDiscountCodes:
    """Tests for discount code validation."""

    def test_valid_discount_code(self):
        """Should validate known discount codes."""
        discount = validate_discount_code("DEMO20")
        assert discount is not None
        assert discount["title"] == "Demo Discount"
        assert discount["type"] == "percentage"
        assert discount["value"] == 20

    def test_discount_code_case_insensitive(self):
        """Discount codes should be case-insensitive."""
        assert validate_discount_code("demo20") is not None
        assert validate_discount_code("Demo20") is not None
        assert validate_discount_code("DEMO20") is not None

    def test_invalid_discount_code(self):
        """Should return None for invalid codes."""
        assert validate_discount_code("INVALID") is None
        assert validate_discount_code("") is None

    def test_all_discount_codes_have_required_fields(self):
        """All discount codes should have required fields."""
        for code, details in DISCOUNT_CODES.items():
            assert "title" in details
            assert "type" in details
            assert "value" in details


class TestFulfillmentOptions:
    """Tests for fulfillment options."""

    def test_fulfillment_options_exist(self):
        """Should have fulfillment options available."""
        options = get_fulfillment_options()
        assert len(options) >= 1

    def test_pickup_option_is_free(self):
        """Pickup option should be free."""
        options = get_fulfillment_options()
        pickup = next((o for o in options if o["id"] == "pickup"), None)
        assert pickup is not None
        assert pickup["price"] == 0

    def test_all_options_have_required_fields(self):
        """All fulfillment options should have required fields."""
        for option in FULFILLMENT_OPTIONS:
            assert "id" in option
            assert "title" in option
            assert "price" in option
            assert option["price"] >= 0
