"""
Settings routes — API key management, user preferences.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_api_keys, save_api_keys, mask_key
from backend.database import get_session, User

router = APIRouter(tags=["settings"])


@router.get("/settings")
async def get_settings(session: AsyncSession = Depends(get_session)):
    """Return current settings with masked API keys."""
    keys = get_api_keys()

    # Get user profile
    result = await session.execute(select(User).where(User.id == 1))
    user = result.scalars().first()

    return {
        "api_keys": {
            "gemini": {
                "configured": bool(keys.gemini_api_key),
                "masked": mask_key(keys.gemini_api_key),
            },
            "anthropic": {
                "configured": bool(keys.anthropic_api_key),
                "masked": mask_key(keys.anthropic_api_key),
            },
        },
        "user_profile": user.to_dict() if user else None,
    }


@router.put("/settings")
async def update_settings(body: dict, session: AsyncSession = Depends(get_session)):
    """Update API keys and/or preferences."""
    # Handle API keys
    gemini_key = body.get("gemini_api_key")
    anthropic_key = body.get("anthropic_api_key")

    if gemini_key is not None or anthropic_key is not None:
        save_api_keys(gemini_key=gemini_key, anthropic_key=anthropic_key)

    return {"status": "updated"}


@router.get("/onboarding/status")
async def onboarding_status(session: AsyncSession = Depends(get_session)):
    """Check if user has completed onboarding."""
    keys = get_api_keys()
    has_keys = bool(keys.gemini_api_key)

    result = await session.execute(select(User).where(User.id == 1))
    user = result.scalars().first()
    has_profile = user is not None and user.technical_level != "semi_technical"

    return {
        "has_api_keys": has_keys,
        "has_profile": has_profile,
        "onboarding_complete": has_keys and has_profile,
    }


@router.post("/onboarding/profile")
async def save_profile(body: dict, session: AsyncSession = Depends(get_session)):
    """Save or update user profile from onboarding."""
    import json

    result = await session.execute(select(User).where(User.id == 1))
    user = result.scalars().first()

    if not user:
        user = User(id=1)
        session.add(user)

    if "technical_level" in body:
        user.technical_level = body["technical_level"]
    if "domain" in body:
        user.domain = body["domain"]
    if "role" in body:
        user.role = body["role"]
    if "stack" in body:
        user.set_stack(body["stack"])
    if "communication_preferences" in body:
        user.set_communication_preferences(body["communication_preferences"])
    if "pet_peeves" in body:
        user.set_pet_peeves(body["pet_peeves"])
    if "positive_patterns" in body:
        user.set_positive_patterns(body["positive_patterns"])

    await session.commit()
    await session.refresh(user)

    return user.to_dict()
