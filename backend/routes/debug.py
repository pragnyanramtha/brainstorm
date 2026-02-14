"""
Debug routes for inspecting system internals.
Retrieve optimized prompts, metadata, and execution details for UI debugging.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session, Message

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/{message_id}")
async def get_message_debug(
    message_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get full debug info for a message."""
    query = select(Message).where(Message.id == message_id)
    result = await session.execute(query)
    msg = result.scalars().first()
    
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    metadata = msg.get_metadata()
    
    # Structure for frontend DebugPanel
    return {
        "message_id": msg.id,
        "optimized_prompt": metadata.get("optimized_prompt"),
        "intake_analysis": {
            "interpreted_intent": metadata.get("interpreted_intent"),
            "task_type": metadata.get("task_type"),
            "complexity": metadata.get("complexity"),
            "confidence_score": metadata.get("confidence_score"),
        },
        "skills_applied": metadata.get("skills_applied", []),
        "mcps_used": metadata.get("mcps_used", []),
        "model_used": metadata.get("model_used"),
        "files_created": metadata.get("files_created", []),
    }
