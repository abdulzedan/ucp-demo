"""Business server - combines all routes for the mock merchant."""

from fastapi import APIRouter

from backend.business.checkout import router as checkout_router
from backend.business.discovery import router as discovery_router

# Create main business router
router = APIRouter(tags=["business"])

# Include sub-routers
router.include_router(discovery_router)
router.include_router(checkout_router)
