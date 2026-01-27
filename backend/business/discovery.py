"""UCP Discovery endpoint for business profile."""

import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.schemas.discovery import create_demo_business_profile

router = APIRouter()


@router.get("/.well-known/ucp")
async def get_ucp_profile() -> JSONResponse:
    """Return the business's UCP profile for discovery.

    This endpoint is the entry point for UCP capability discovery.
    Platforms fetch this profile to learn:
    - What services/transports the business supports
    - What capabilities are available (Checkout, Fulfillment, etc.)
    - What payment handlers are configured

    Returns:
        JSONResponse: The business's UCP profile
    """
    business_url = os.getenv("BUSINESS_URL", "http://localhost:8000")
    business_name = os.getenv("BUSINESS_NAME", "Cymbal Coffee Shop")

    profile = create_demo_business_profile(
        business_url=business_url,
        business_name=business_name,
    )

    # Convert to dict and use proper JSON serialization
    profile_dict = profile.model_dump(by_alias=True, exclude_none=True)

    return JSONResponse(
        content=profile_dict,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
        },
    )


@router.get("/api/v1/profile")
async def get_profile_info() -> dict:
    """Return basic business information for display purposes.

    This is a convenience endpoint, not part of UCP spec.
    """
    return {
        "name": os.getenv("BUSINESS_NAME", "Cymbal Coffee Shop"),
        "description": "Your neighborhood coffee shop, now UCP-enabled!",
        "logo_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=100",
        "ucp_profile_url": "/.well-known/ucp",
        "capabilities": [
            "dev.ucp.shopping.checkout",
            "dev.ucp.shopping.fulfillment",
            "dev.ucp.shopping.discount",
        ],
    }
