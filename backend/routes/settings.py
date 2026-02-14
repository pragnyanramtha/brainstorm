"""
Settings and onboarding routes.
Manage API keys, user profile, and system status.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session, User
from backend.config import get_api_keys, save_api_keys, mask_key
from backend.memory.user_profile import get_user_profile, ensure_user_exists, extract_profile_from_chat

router = APIRouter(prefix="/api", tags=["settings"])


class APIKeyUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None


class ProfileUpdate(BaseModel):
    technical_level: Optional[str] = None
    domain: Optional[str] = None
    role: Optional[str] = None
    stack: Optional[list[str]] = None
    communication_preferences: Optional[dict] = None
    pet_peeves: Optional[list[str]] = None
    positive_patterns: Optional[list[str]] = None


@router.get("/settings")
async def get_settings_route(session: AsyncSession = Depends(get_session)):
    """Get current settings (masked keys, profile)."""
    keys = get_api_keys()
    
    profile = await get_user_profile(session)
    
    return {
        "api_keys": {
            "gemini": {
                "configured": bool(keys.gemini_api_key),
                "masked": mask_key(keys.gemini_api_key)
            },
            "anthropic": {
                "configured": bool(keys.anthropic_api_key),
                "masked": mask_key(keys.anthropic_api_key)
            }
        },
        "user_profile": profile
    }


@router.put("/settings")
async def update_settings_key(
    data: APIKeyUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update API keys."""
    save_api_keys(
        gemini_key=data.gemini_api_key,
        anthropic_key=data.anthropic_api_key
    )
    return {"status": "updated"}


@router.get("/onboarding/status")
async def onboarding_status(session: AsyncSession = Depends(get_session)):
    """Check if onboarding is needed."""
    keys = get_api_keys()
    profile = await get_user_profile(session)
    
    has_keys = bool(keys.gemini_api_key)
    has_profile = bool(profile and profile.get("technical_level"))
    
    return {
        "has_api_keys": has_keys,
        "has_profile": has_profile,
        "onboarding_complete": has_keys and has_profile
    }


@router.post("/onboarding/profile")
async def create_profile(
    data: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Manually create/update user profile."""
    user = await ensure_user_exists(session)
    
    if data.technical_level:
        user.technical_level = data.technical_level
    if data.domain:
        user.domain = data.domain
    if data.role:
        user.role = data.role
    if data.stack is not None:
        user.set_stack(data.stack)
    if data.communication_preferences:
        user.set_communication_preferences(data.communication_preferences)
    if data.pet_peeves is not None:
        user.set_pet_peeves(data.pet_peeves)
    if data.positive_patterns is not None:
        user.set_positive_patterns(data.positive_patterns)
        
    await session.commit()
    await session.refresh(user)
    
    return user.to_dict()
