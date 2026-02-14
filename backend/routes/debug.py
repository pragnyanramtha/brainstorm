"""
Debug routes — view optimized prompts and metadata for transparency.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session, Message

router = APIRouter(tags=["debug"])


@router.get("/debug/{message_id}")
async def get_debug_info(message_id: str, session: AsyncSession = Depends(get_session)):
    """Return the optimized prompt and full metadata for a specific message."""
    result = await session.execute(select(Message).where(Message.id == message_id))
    message = result.scalars().first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    metadata = message.get_metadata()

    return {
        "message_id": message.id,
        "role": message.role,
        "content": message.content,
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
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }
