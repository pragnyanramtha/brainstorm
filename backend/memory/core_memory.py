"""
Persistent core memory — facts, preferences, project context.
Supports recall (retrieve relevant memories) and remember (extract new memories).
"""
import json
import traceback
import datetime
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from rich.console import Console

from backend.config import get_api_keys, ModelConfig
from backend.database import CoreMemory

console = Console()


async def recall_memories(
    task_type: str = None,
    project_id: str = None,
    session: AsyncSession = None,
    max_memories: int = 20,
) -> list[dict]:
    """
    Retrieve relevant core memories for the current task.

    Logic:
    - Always include: identity and preference memories
    - For code tasks: include technical memories
    - For continuing projects: include project_context memories
    - Sort by importance * recency_decay
    - Cap at max_memories
    """
    if not session:
        return []

    try:
        # Build query conditions
        conditions = [CoreMemory.active == True]

        # Always get identity and preference
        category_conditions = [
            CoreMemory.category.in_(["identity", "preference"]),
        ]

        # Add technical for code tasks
        if task_type in ("code", "debugging", "system_design"):
            category_conditions.append(CoreMemory.category == "technical")

        # Add project context if we have a project
        if project_id:
            category_conditions.append(
                and_(
                    CoreMemory.category == "project_context",
                    CoreMemory.source_session_id == project_id,
                )
            )

        # Also get relationship memories (always useful)
        category_conditions.append(CoreMemory.category == "relationship")

        result = await session.execute(
            select(CoreMemory)
            .where(
                and_(
                    CoreMemory.active == True,
                    or_(*category_conditions),
                )
            )
            .order_by(CoreMemory.importance.desc(), CoreMemory.last_accessed.desc())
            .limit(max_memories)
        )

        memories = result.scalars().all()

        # Update access counts
        for mem in memories:
            mem.access_count += 1
            mem.last_accessed = datetime.datetime.utcnow()

        await session.commit()

        memory_dicts = [m.to_dict() for m in memories]

        if memory_dicts:
            console.print(f"[blue]Recalled {len(memory_dicts)} core memories[/blue]")

        return memory_dicts

    except Exception as e:
        console.print(f"[red]Memory recall failed: {e}[/red]")
        return []


async def remember(
    user_message: str,
    assistant_response: str,
    project_id: str = None,
    session: AsyncSession = None,
):
    """
    Extract new memories from a conversation using Gemini Flash.
    Called in the background after each response.

    Deduplicates against existing memories before storing.
    """
    if not session:
        return

    keys = get_api_keys()
    if not keys.gemini_api_key:
        return

    try:
        from google import genai

        # Get existing memories for deduplication
        result = await session.execute(
            select(CoreMemory).where(CoreMemory.active == True).limit(50)
        )
        existing = result.scalars().all()
        existing_contents = [m.content.lower() for m in existing]

        # Build the extraction prompt
        extraction_prompt = f"""Analyze this conversation and extract any new facts worth remembering about the user.

CONVERSATION:
User: {user_message}
Assistant: {assistant_response}

EXISTING MEMORIES (do NOT re-extract these):
{chr(10).join(f'- [{m.category}] {m.content}' for m in existing[:30])}

RULES:
1. Only extract genuinely useful, NON-OBVIOUS facts
2. Categories: identity, preference, project_context, technical, relationship
3. DO NOT extract: trivial facts, things already in existing memories, generic observations
4. Each memory should be a clear, standalone statement
5. Return empty list if nothing new is worth remembering

Return JSON:
{{
  "memories": [
    {{"category": "technical", "content": "Uses Python 3.12 with FastAPI for backend projects", "importance": 0.7}},
  ]
}}

Return {{"memories": []}} if nothing new to remember."""

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
        new_memories = data.get("memories", [])

        if not new_memories:
            return

        # Importance defaults by category
        importance_defaults = {
            "identity": 0.8,
            "preference": 0.7,
            "project_context": 0.5,
            "technical": 0.6,
            "relationship": 0.6,
        }

        stored_count = 0
        for mem_data in new_memories:
            content = mem_data.get("content", "").strip()
            category = mem_data.get("category", "technical")

            if not content or len(content) < 5:
                continue

            # Validate category
            if category not in importance_defaults:
                category = "technical"

            # Deduplication: check if similar content exists
            content_lower = content.lower()
            is_duplicate = False
            for existing_content in existing_contents:
                # Simple keyword overlap check
                content_words = set(content_lower.split())
                existing_words = set(existing_content.split())
                if len(content_words) > 3:
                    overlap = len(content_words & existing_words) / len(content_words)
                    if overlap > 0.7:
                        is_duplicate = True
                        break

            if is_duplicate:
                continue

            importance = mem_data.get("importance", importance_defaults.get(category, 0.5))
            importance = max(0.0, min(1.0, float(importance)))

            memory = CoreMemory(
                category=category,
                content=content,
                source_session_id=project_id,
                importance=importance,
            )
            session.add(memory)
            existing_contents.append(content_lower)
            stored_count += 1

        if stored_count > 0:
            await session.commit()
            console.print(f"[green]Stored {stored_count} new core memories[/green]")

    except Exception as e:
        console.print(f"[red]Memory extraction failed: {e}[/red]")
        console.print(traceback.format_exc())
