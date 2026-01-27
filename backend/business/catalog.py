"""Product catalog for the demo coffee shop."""

from backend.schemas.checkout import Item

# Demo product catalog for "Cymbal Coffee Shop"
CATALOG: dict[str, Item] = {
    "coffee_small": Item(
        id="coffee_small",
        title="Small Coffee",
        description="8oz freshly brewed coffee",
        image_url="/images/coffee.jpeg",
        price=299,
        currency="USD",
    ),
    "coffee_medium": Item(
        id="coffee_medium",
        title="Medium Coffee",
        description="12oz freshly brewed coffee",
        image_url="/images/coffee.jpeg",
        price=399,
        currency="USD",
    ),
    "coffee_large": Item(
        id="coffee_large",
        title="Large Coffee",
        description="16oz freshly brewed coffee",
        image_url="/images/coffee.jpeg",
        price=499,
        currency="USD",
    ),
    "latte_medium": Item(
        id="latte_medium",
        title="Medium Latte",
        description="12oz espresso with steamed milk",
        image_url="/images/latte.jpeg",
        price=549,
        currency="USD",
    ),
    "latte_large": Item(
        id="latte_large",
        title="Large Latte",
        description="16oz espresso with steamed milk",
        image_url="/images/latte.jpeg",
        price=649,
        currency="USD",
    ),
    "cappuccino": Item(
        id="cappuccino",
        title="Cappuccino",
        description="Espresso with foamed milk",
        image_url="/images/cappuccino.jpeg",
        price=549,
        currency="USD",
    ),
    "espresso_single": Item(
        id="espresso_single",
        title="Single Espresso",
        description="Single shot of espresso",
        image_url="/images/espresso.jpeg",
        price=299,
        currency="USD",
    ),
    "espresso_double": Item(
        id="espresso_double",
        title="Double Espresso",
        description="Double shot of espresso",
        image_url="/images/espresso.jpeg",
        price=399,
        currency="USD",
    ),
    "muffin_blueberry": Item(
        id="muffin_blueberry",
        title="Blueberry Muffin",
        description="Fresh baked blueberry muffin",
        image_url="/images/muffin_blueberry.jpeg",
        price=349,
        currency="USD",
    ),
    "muffin_chocolate": Item(
        id="muffin_chocolate",
        title="Chocolate Chip Muffin",
        description="Fresh baked chocolate chip muffin",
        image_url="/images/muffin_chocolate.jpeg",
        price=349,
        currency="USD",
    ),
    "croissant": Item(
        id="croissant",
        title="Butter Croissant",
        description="Flaky butter croissant",
        image_url="/images/croissant.jpeg",
        price=399,
        currency="USD",
    ),
    "bagel": Item(
        id="bagel",
        title="Everything Bagel",
        description="Everything bagel with cream cheese",
        image_url="/images/bagel.jpeg",
        price=449,
        currency="USD",
    ),
}

# Available discount codes
DISCOUNT_CODES: dict[str, dict] = {
    "DEMO20": {
        "title": "Demo Discount",
        "type": "percentage",
        "value": 20,  # 20% off
    },
    "SAVE5": {
        "title": "Save $5",
        "type": "fixed",
        "value": 500,  # $5 off in cents
    },
    "FREESHIP": {
        "title": "Free Shipping",
        "type": "free_shipping",
        "value": 0,
    },
}

# Fulfillment options
FULFILLMENT_OPTIONS = [
    {
        "id": "pickup",
        "title": "In-Store Pickup",
        "description": "Pick up at our location",
        "price": 0,
        "estimated_delivery": "Ready in 15 minutes",
    },
    {
        "id": "standard",
        "title": "Standard Delivery",
        "description": "Delivered to your door",
        "price": 499,
        "estimated_delivery": "30-45 minutes",
    },
    {
        "id": "express",
        "title": "Express Delivery",
        "description": "Priority delivery",
        "price": 899,
        "estimated_delivery": "15-20 minutes",
    },
]


def get_product(product_id: str) -> Item | None:
    """Get a product by ID."""
    return CATALOG.get(product_id)


def get_all_products() -> list[Item]:
    """Get all products in the catalog."""
    return list(CATALOG.values())


def validate_discount_code(code: str) -> dict | None:
    """Validate a discount code and return its details."""
    return DISCOUNT_CODES.get(code.upper())


def get_fulfillment_options() -> list[dict]:
    """Get available fulfillment options."""
    return FULFILLMENT_OPTIONS
