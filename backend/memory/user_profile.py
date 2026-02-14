"""
User profiling and preference learning.
Handles profile CRUD and natural language profile extraction.
"""
import json
import traceback
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from rich.console import Console

from backend.config import get_api_keys, ModelConfig
from backend.database import User

console = Console()


async def get_user_profile(session: AsyncSession) -> Optional[dict]:
    """Get the single user's profile from DB."""
    try:
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalars().first()
        return user.to_dict() if user else None
    except Exception as e:
        console.print(f"[red]Failed to load user profile: {e}[/red]")
        return None


async def ensure_user_exists(session: AsyncSession) -> User:
    """Ensure a user record exists, create if not."""
    result = await session.execute(select(User).where(User.id == 1))
    user = result.scalars().first()
    if not user:
        user = User(id=1)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def update_interaction_count(session: AsyncSession):
    """Increment the user's interaction count."""
    try:
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalars().first()
        if user:
            user.interaction_count += 1
            await session.commit()
    except Exception as e:
        console.print(f"[red]Failed to update interaction count: {e}[/red]")


async def extract_profile_from_chat(
    user_message: str,
    session: AsyncSession,
) -> Optional[dict]:
    """
    Extract structured profile data from a natural language response.
    Used during onboarding when the user answers profiling questions conversationally.
    """
    keys = get_api_keys()
    if not keys.gemini_api_key:
        return None

    try:
        from google import genai

        extraction_prompt = f"""Extract user profile information from this natural language response.

USER'S RESPONSE:
{user_message}

Extract what you can infer and return as JSON:
{{
  "technical_level": "non_technical | semi_technical | technical | expert",
  "domain": "their primary domain (e.g., 'frontend development', 'data science')",
  "role": "their role (e.g., 'senior engineer', 'student', 'product manager')",
  "stack": ["list", "of", "technologies they use"],
  "communication_preferences": {{
    "detail_level": "brief | balanced | detailed",
    "tone": "casual | friendly | professional | technical",
    "format": "markdown | plain | structured"
  }},
  "pet_peeves": ["things they don't like in AI responses"],
  "positive_patterns": ["things they appreciate in responses"]
}}

RULES:
- Only include fields you can CONFIDENTLY extract
- For fields you can't determine, use these defaults:
  - technical_level: "semi_technical"
  - communication_preferences: {{"detail_level": "balanced", "tone": "friendly", "format": "markdown"}}
- Infer technical_level from their language: if they mention specific technologies, APIs, or use technical jargon → "technical" or "expert"
- Be conservative — don't over-infer from limited data

Return ONLY the JSON object."""

        client = genai.Client(api_key=keys.gemini_api_key)

        response = client.models.generate_content(
            model=ModelConfig.MEMORY_MODEL,
            contents=extraction_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        data = json.loads(response.text.strip())

        # Update user profile
        user = await ensure_user_exists(session)

        if "technical_level" in data:
            valid_levels = {"non_technical", "semi_technical", "technical", "expert"}
            if data["technical_level"] in valid_levels:
                user.technical_level = data["technical_level"]

        if "domain" in data and data["domain"]:
            user.domain = data["domain"]

        if "role" in data and data["role"]:
            user.role = data["role"]

        if "stack" in data and isinstance(data["stack"], list):
            user.set_stack(data["stack"])

        if "communication_preferences" in data:
            user.set_communication_preferences(data["communication_preferences"])

        if "pet_peeves" in data and isinstance(data["pet_peeves"], list):
            user.set_pet_peeves(data["pet_peeves"])

        if "positive_patterns" in data and isinstance(data["positive_patterns"], list):
            user.set_positive_patterns(data["positive_patterns"])

        await session.commit()
        await session.refresh(user)

        console.print(f"[green]Profile extracted: {user.technical_level}, {user.domain}, {user.role}[/green]")

        return user.to_dict()

    except Exception as e:
        console.print(f"[red]Profile extraction failed: {e}[/red]")
        console.print(traceback.format_exc())
        return None
