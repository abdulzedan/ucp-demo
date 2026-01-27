"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestDiscoveryEndpoint:
    """Tests for UCP discovery endpoint."""

    def test_discovery_returns_200(self, client):
        """Discovery endpoint should return 200."""
        response = client.get("/.well-known/ucp")
        assert response.status_code == 200

    def test_discovery_has_ucp_metadata(self, client):
        """Discovery response should have UCP metadata."""
        response = client.get("/.well-known/ucp")
        data = response.json()
        assert "ucp" in data
        assert "version" in data["ucp"]

    def test_discovery_has_capabilities(self, client):
        """Discovery should list capabilities."""
        response = client.get("/.well-known/ucp")
        data = response.json()
        assert "capabilities" in data["ucp"]
        # Should have checkout capability
        assert "dev.ucp.shopping.checkout" in data["ucp"]["capabilities"]

    def test_discovery_has_payment_handlers(self, client):
        """Discovery should list payment handlers."""
        response = client.get("/.well-known/ucp")
        data = response.json()
        assert "payment_handlers" in data["ucp"]


class TestProductsEndpoint:
    """Tests for products endpoint."""

    def test_get_products_returns_200(self, client):
        """Products endpoint should return 200."""
        response = client.get("/api/v1/products")
        assert response.status_code == 200

    def test_get_products_returns_list(self, client):
        """Products endpoint should return a list."""
        response = client.get("/api/v1/products")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_products_have_required_fields(self, client):
        """Each product should have required fields."""
        response = client.get("/api/v1/products")
        data = response.json()
        for product in data:
            assert "id" in product
            assert "title" in product
            assert "price" in product


class TestCheckoutEndpoints:
    """Tests for checkout endpoints."""

    def test_create_checkout_returns_200(self, client):
        """Create checkout should return 200."""
        response = client.post(
            "/api/v1/checkout-sessions",
            json={
                "line_items": [{"product_id": "latte_medium", "quantity": 1}]
            },
        )
        assert response.status_code == 200

    def test_create_checkout_returns_session(self, client):
        """Create checkout should return session with ID."""
        response = client.post(
            "/api/v1/checkout-sessions",
            json={
                "line_items": [{"product_id": "latte_medium", "quantity": 1}]
            },
        )
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert "line_items" in data
        assert data["status"] == "incomplete"

    def test_create_checkout_calculates_totals(self, client):
        """Create checkout should calculate totals."""
        response = client.post(
            "/api/v1/checkout-sessions",
            json={
                "line_items": [{"product_id": "latte_medium", "quantity": 2}]
            },
        )
        data = response.json()
        assert "totals" in data
        assert data["totals"]["subtotal"] == 1098  # 549 * 2

    def test_get_checkout_returns_session(self, client):
        """Get checkout should return existing session."""
        # Create first
        create_response = client.post(
            "/api/v1/checkout-sessions",
            json={
                "line_items": [{"product_id": "coffee_small", "quantity": 1}]
            },
        )
        checkout_id = create_response.json()["id"]

        # Get it back
        get_response = client.get(f"/api/v1/checkout-sessions/{checkout_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == checkout_id

    def test_get_checkout_not_found(self, client):
        """Get checkout should return 404 for non-existent session."""
        response = client.get("/api/v1/checkout-sessions/nonexistent-id")
        assert response.status_code == 404

    def test_update_checkout_with_fulfillment(self, client):
        """Update checkout should accept fulfillment selection."""
        # Create first
        create_response = client.post(
            "/api/v1/checkout-sessions",
            json={
                "line_items": [{"product_id": "latte_medium", "quantity": 1}]
            },
        )
        checkout_id = create_response.json()["id"]

        # Update with fulfillment
        update_response = client.put(
            f"/api/v1/checkout-sessions/{checkout_id}",
            json={
                "line_items": [{"product_id": "latte_medium", "quantity": 1}],
                "fulfillment": {"selected_option_id": "pickup"},
            },
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["fulfillment"]["selected_option_id"] == "pickup"
        # With pickup selected, should be ready for complete
        assert data["status"] == "ready_for_complete"

    def test_update_checkout_with_discount(self, client):
        """Update checkout should apply valid discount codes."""
        # Create first
        create_response = client.post(
            "/api/v1/checkout-sessions",
            json={
                "line_items": [{"product_id": "latte_medium", "quantity": 1}]
            },
        )
        checkout_id = create_response.json()["id"]

        # Update with discount
        update_response = client.put(
            f"/api/v1/checkout-sessions/{checkout_id}",
            json={
                "line_items": [{"product_id": "latte_medium", "quantity": 1}],
                "discount_codes": ["DEMO20"],
            },
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert len(data["discounts"]) == 1
        assert data["discounts"][0]["code"] == "DEMO20"


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
