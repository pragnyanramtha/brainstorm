"""
Chat routes — WebSocket endpoint for real-time chat and POST endpoint for simple chat.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session

router = APIRouter(tags=["chat"])


@router.websocket("/ws/{project_id}")
async def websocket_chat(websocket: WebSocket, project_id: str):
    """Main WebSocket chat endpoint. Handles the full orchestrator pipeline."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Stub: echo back for now — will be replaced with full orchestrator in Task 2-3
            msg_type = data.get("type", "message")

            if msg_type == "message":
                await websocket.send_json({
                    "type": "status",
                    "state": "analyzing",
                })
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": f"[Stub] Received: {data.get('content', '')}",
                    "metadata": {},
                })
            elif msg_type == "clarification_response":
                await websocket.send_json({
                    "type": "message",
                    "role": "assistant",
                    "content": "[Stub] Clarification received, processing...",
                    "metadata": {},
                })
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass


@router.post("/chat/{project_id}")
async def post_chat(project_id: str, body: dict, session: AsyncSession = Depends(get_session)):
    """Simple POST chat endpoint for non-WebSocket clients."""
    content = body.get("content", "")
    return {
        "type": "message",
        "role": "assistant",
        "content": f"[Stub] Received: {content}",
        "metadata": {},
    }
