"""WebSocket server for real-time protocol visualization."""

import asyncio
import json
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.visualizer.events import (
    ProtocolEvent,
    event_store,
    format_event_for_display,
)

router = APIRouter(tags=["visualizer"])

# Connected WebSocket clients
connected_clients: Set[WebSocket] = set()


async def broadcast_event(event: ProtocolEvent) -> None:
    """Broadcast an event to all connected clients."""
    if not connected_clients:
        return

    message = json.dumps(
        {
            "type": "event",
            "data": format_event_for_display(event),
        }
    )

    # Send to all clients
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            disconnected.add(client)

    # Remove disconnected clients
    connected_clients.difference_update(disconnected)


def on_event(event: ProtocolEvent) -> None:
    """Callback for new events - schedules broadcast."""
    asyncio.create_task(broadcast_event(event))


# Clear any existing subscribers before subscribing (handles hot-reload)
# This ensures only one broadcast callback is registered
event_store._subscribers.clear()
event_store.subscribe(on_event)


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time event streaming.

    Clients connect here to receive protocol events as they happen.
    """
    await websocket.accept()
    connected_clients.add(websocket)

    try:
        # Send initial state
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "message": "Connected to UCP event stream",
                }
            )
        )

        # Send recent events
        recent_events = event_store.get_events(limit=20)
        for event in recent_events:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "event",
                        "data": format_event_for_display(event),
                    }
                )
            )

        # Keep connection alive
        while True:
            try:
                # Wait for messages (heartbeat or commands)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,
                )

                # Handle commands
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif message.get("type") == "get_events":
                        events = event_store.get_events(limit=message.get("limit", 50))
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "events_list",
                                    "data": [
                                        format_event_for_display(e) for e in events
                                    ],
                                }
                            )
                        )
                    elif message.get("type") == "clear":
                        event_store.clear()
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "cleared",
                                    "message": "Event store cleared",
                                }
                            )
                        )
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_text(json.dumps({"type": "keepalive"}))

    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(websocket)


@router.get("/api/v1/events")
async def get_events(limit: int = 50) -> dict:
    """Get recent protocol events via REST."""
    events = event_store.get_events(limit=limit)
    return {
        "events": [format_event_for_display(e) for e in events],
        "count": len(events),
    }


@router.post("/api/v1/events/clear")
async def clear_events() -> dict:
    """Clear all events."""
    event_store.clear()
    return {"status": "cleared"}
