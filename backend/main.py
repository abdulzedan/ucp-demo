"""Main FastAPI application for UCP Demo."""

import json
import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Load environment variables
load_dotenv()

from backend.business.server import router as business_router
from backend.platform.chat import router as platform_router
from backend.visualizer.websocket import router as visualizer_router
from backend.visualizer.events import (
    event_store,
    capture_request,
    capture_response,
    EventType,
    format_event_for_display,
)


def get_event_type(path: str, method: str) -> EventType | None:
    """Determine the event type based on path and method.

    NOTE: All UCP events are now emitted by the agent tools in agent.py.
    This middleware is disabled to prevent duplicate event capture.
    The agent emits events with better context (at tool invocation time
    rather than raw HTTP level).
    """
    # All events are now handled by agent tools - disable middleware capture
    # to prevent duplicate events in the visualizer
    return None


class EventCaptureMiddleware(BaseHTTPMiddleware):
    """Middleware to capture UCP protocol events."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Only capture UCP-related paths
        event_type = get_event_type(path, method)
        if not event_type:
            return await call_next(request)

        # Capture request
        start_time = time.time()
        try:
            body = await request.body()
            body_json = json.loads(body) if body else None
        except Exception:
            body_json = None

        request_id = capture_request(
            event_type=event_type,
            method=method,
            path=path,
            headers=dict(request.headers),
            body=body_json,
        )

        # Call the actual endpoint
        response = await call_next(request)

        # Capture response
        duration_ms = (time.time() - start_time) * 1000

        # Read response body for capture
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        try:
            response_json = json.loads(response_body) if response_body else None
        except Exception:
            response_json = None

        capture_response(
            request_id=request_id,
            event_type=event_type,
            method=method,
            path=path,
            status_code=response.status_code,
            body=response_json,
            duration_ms=round(duration_ms, 2),
        )

        # Return a new response with the same body
        return JSONResponse(
            content=response_json,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("=" * 60)
    print("UCP Demo Server Starting...")
    print(f"Business: {os.getenv('BUSINESS_NAME', 'Cymbal Coffee Shop')}")
    print(f"Discovery endpoint: http://localhost:8000/.well-known/ucp")
    print("=" * 60)
    yield
    # Shutdown
    print("UCP Demo Server Shutting Down...")


app = FastAPI(
    title="UCP Demo",
    description="Interactive demonstration of the Universal Commerce Protocol",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Demo only - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event capture middleware for UCP protocol visualization
app.add_middleware(EventCaptureMiddleware)

# Include routers
app.include_router(business_router)
app.include_router(platform_router)
app.include_router(visualizer_router)


@app.get("/")
async def root():
    """Root endpoint with demo information."""
    return {
        "name": "UCP Demo",
        "description": "Interactive demonstration of the Universal Commerce Protocol",
        "version": "0.1.0",
        "links": {
            "discovery": "/.well-known/ucp",
            "products": "/api/v1/products",
            "docs": "/docs",
            "redoc": "/redoc",
        },
        "demo_scenarios": [
            "1. Fetch /.well-known/ucp to discover capabilities",
            "2. Browse /api/v1/products for available items",
            "3. POST /api/v1/checkout-sessions to start checkout",
            "4. PUT /api/v1/checkout-sessions/{id} to update cart",
            "5. POST /api/v1/checkout-sessions/{id}/complete to finish",
        ],
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "status": "requires_escalation",
            "messages": [
                {
                    "type": "error",
                    "code": "internal_error",
                    "content": str(exc),
                    "severity": "requires_buyer_input",
                }
            ],
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "true").lower() == "true",
    )
