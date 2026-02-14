"""
Feedback routes.
Collect user feedback on responses to improve skill scoring.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session, Feedback, Message, Project, Skill

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackCreate(BaseModel):
    message_id: str
    project_id: str
    rating: int  # 1-5
    comment: str = None


@router.post("")
async def submit_feedback(
    data: FeedbackCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Submit feedback on a message.
    Also updates effectiveness scores for skills used in that message.
    """
    # Verify message exists
    msg_result = await session.execute(
        select(Message).where(Message.id == data.message_id)
    )
    msg = msg_result.scalars().first()
    
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    metadata = msg.get_metadata()
    skills_used_names = metadata.get("skills_applied", [])
    model_used = metadata.get("model_used")

    # Save feedback
    feedback = Feedback(
        message_id=data.message_id,
        project_id=data.project_id,
        rating=data.rating,
        comment=data.comment,
        skills_used=msg.metadata_json,  # Store full metadata snapshot
        model_used=model_used,
    )
    session.add(feedback)

    # Update skill scores
    # If rating >= 4, positive feedback. If <= 2, negative.
    if data.rating >= 4 or data.rating <= 2:
        skills_result = await session.execute(
            select(Skill).where(Skill.name.in_(skills_used_names))
        )
        skills = skills_result.scalars().all()

        for skill in skills:
            if data.rating >= 4:
                skill.positive_feedback_count += 1
                # Boost score slightly
                skill.effectiveness_score = min(1.0, skill.effectiveness_score + 0.05)
            else:
                skill.negative_feedback_count += 1
                # Penalty
                skill.effectiveness_score = max(0.1, skill.effectiveness_score - 0.05)

    await session.commit()
    
    return {"status": "feedback_saved"}
