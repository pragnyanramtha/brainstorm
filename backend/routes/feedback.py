"""
Feedback routes — user ratings and comments for responses.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session, Feedback, Message, Skill

router = APIRouter(tags=["feedback"])


@router.post("/feedback")
async def submit_feedback(body: dict, session: AsyncSession = Depends(get_session)):
    """Submit rating (1-5) + optional comment for a message. Updates skill effectiveness."""
    message_id = body.get("message_id")
    project_id = body.get("project_id")
    rating = body.get("rating")
    comment = body.get("comment")

    if not message_id or not project_id or not rating:
        raise HTTPException(status_code=400, detail="message_id, project_id, and rating are required")

    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # Get message metadata for skills used
    result = await session.execute(select(Message).where(Message.id == message_id))
    message = result.scalars().first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    metadata = message.get_metadata()
    skills_used = metadata.get("skills_applied", [])
    model_used = metadata.get("model_used", "unknown")

    # Save feedback
    fb = Feedback(
        message_id=message_id,
        project_id=project_id,
        rating=rating,
        comment=comment,
        skills_used=json.dumps(skills_used),
        model_used=model_used,
    )
    session.add(fb)

    # Update skill effectiveness scores based on feedback
    if skills_used:
        for skill_name in skills_used:
            skill_result = await session.execute(select(Skill).where(Skill.name == skill_name))
            skill = skill_result.scalars().first()
            if skill:
                if rating >= 4:
                    skill.positive_feedback_count += 1
                elif rating <= 2:
                    skill.negative_feedback_count += 1

                total = skill.positive_feedback_count + skill.negative_feedback_count
                if total > 0:
                    skill.effectiveness_score = skill.positive_feedback_count / total

    await session.commit()

    return {"status": "saved", "id": fb.id}
