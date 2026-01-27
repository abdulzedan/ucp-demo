"""Chat API for the shopping agent."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.platform.agent import ShoppingAgent, _reset_emitted_events
from backend.visualizer.events import event_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["platform"])

# Global agent instance (demo purposes - in production use proper session management)
_agents: dict[str, ShoppingAgent] = {}


class ProductDisplay(BaseModel):
    """Product for display in chat."""

    id: str
    title: str
    description: str | None = None
    price: str
    image_url: str | None = None


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    session_id: str
    products: list[ProductDisplay] | None = None
    show_products: bool = False
    checkout_session: dict[str, Any] | None = None


def get_agent(session_id: str) -> ShoppingAgent:
    """Get or create an agent for the session."""
    if session_id not in _agents:
        _agents[session_id] = ShoppingAgent()
    return _agents[session_id]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a message to the shopping agent.

    The agent will understand natural language requests and
    execute UCP operations to fulfill them.
    """
    agent = get_agent(request.session_id)

    try:
        response, products = await agent.chat_with_products(
            request.message, request.session_id
        )

        product_displays = None
        show_products = False

        if products:
            show_products = True
            product_displays = [
                ProductDisplay(
                    id=p["id"],
                    title=p["title"],
                    description=p.get("description"),
                    price=f"${p['price']/100:.2f}",
                    image_url=p.get("image_url"),
                )
                for p in products
            ]

        # Fetch the current checkout session if it exists
        checkout_session_data = None
        checkout_id = await agent.get_checkout_id(request.session_id)
        if checkout_id:
            try:
                checkout = agent.ucp_client.get_checkout(checkout_id)
                checkout_session_data = checkout.model_dump(mode="json")
            except Exception:
                pass  # Checkout may have expired or been completed

        return ChatResponse(
            response=response,
            session_id=request.session_id,
            products=product_displays,
            show_products=show_products,
            checkout_session=checkout_session_data,
        )
    except Exception as e:
        logger.exception(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/reset")
async def reset_chat(session_id: str = "default") -> dict:
    """Reset the chat session and create a new agent."""
    if session_id in _agents:
        del _agents[session_id]
    # Reset the emitted events tracker so discovery events fire again
    _reset_emitted_events()
    # Clear the event store to prevent duplicate events in visualizer
    event_store.clear()
    return {"status": "reset", "session_id": session_id}


@router.get("/chat/status")
async def chat_status(session_id: str = "default") -> dict:
    """Get the status of the chat session."""
    if session_id not in _agents:
        return {"status": "no_session", "session_id": session_id}

    agent = _agents[session_id]
    checkout_id = await agent.get_checkout_id(session_id)
    return {
        "status": "active",
        "session_id": session_id,
        "discovered": agent._discovered,
        "has_checkout": checkout_id is not None,
        "checkout_id": checkout_id,
    }
