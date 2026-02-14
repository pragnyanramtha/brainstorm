"""
Skill selection logic — queries DB, ranks skills, applies user profile adjustments.
"""
import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from rich.console import Console

from backend.database import Skill

console = Console()


async def select_skills(
    task_type: str,
    complexity: int,
    user_profile: Optional[dict] = None,
    session: AsyncSession = None,
) -> list[dict]:
    """
    Select the most relevant skills for this task.

    Logic:
    1. Filter: task_type matches AND complexity in range AND active
    2. Sort by effectiveness_score DESC
    3. Take top 5
    4. Adjust for user profile preferences
    5. Return skills with implementation templates
    """
    if not session:
        return []

    try:
        # Get all active skills
        result = await session.execute(
            select(Skill).where(Skill.active == True)
        )
        all_skills = result.scalars().all()

        # Filter and score
        candidates = []
        for skill in all_skills:
            # Check task type match
            best_for = skill.get_best_for_task_types()
            task_matches = task_type in best_for or not best_for  # empty means all tasks

            # Check complexity range
            in_complexity_range = skill.complexity_range_min <= complexity <= skill.complexity_range_max

            if task_matches and in_complexity_range:
                # Calculate a relevance score
                score = skill.effectiveness_score

                # Boost if task type is a direct match
                if task_type in best_for:
                    score += 0.2

                # Boost for skills with more positive feedback
                if skill.usage_count > 0:
                    feedback_ratio = skill.positive_feedback_count / max(1, skill.positive_feedback_count + skill.negative_feedback_count)
                    score += feedback_ratio * 0.1

                candidates.append({
                    "skill": skill,
                    "score": score,
                })

        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # Take top 5
        selected = candidates[:5]

        # User profile adjustments
        if user_profile:
            selected = _apply_profile_adjustments(selected, user_profile, task_type, all_skills)

        # Convert to dicts and update usage counts
        result_skills = []
        for item in selected:
            skill = item["skill"]
            skill.usage_count += 1
            result_skills.append(skill.to_dict())

        await session.commit()

        skill_names = [s["name"] for s in result_skills]
        console.print(f"[blue]Skills selected: {', '.join(skill_names)}[/blue]")

        return result_skills

    except Exception as e:
        console.print(f"[red]Skill selection failed: {e}[/red]")
        return []


def _apply_profile_adjustments(
    selected: list,
    user_profile: dict,
    task_type: str,
    all_skills: list,
) -> list:
    """Apply user profile-based skill adjustments."""
    selected_names = {item["skill"].name for item in selected}

    # Expert users or brief preference → always include concise_mode
    technical_level = user_profile.get("technical_level", "semi_technical")
    prefs = user_profile.get("communication_preferences", {})
    wants_concise = (
        technical_level == "expert"
        or prefs.get("detail_level") == "brief"
    )

    if wants_concise and "concise_mode" not in selected_names:
        for skill in all_skills:
            if skill.name == "concise_mode" and skill.active:
                selected.append({"skill": skill, "score": 0.9})
                selected_names.add("concise_mode")
                break

    # Code tasks for technical users → include error_handling_focus
    if task_type == "code" and technical_level in ("technical", "expert"):
        if "error_handling_focus" not in selected_names:
            for skill in all_skills:
                if skill.name == "error_handling_focus" and skill.active:
                    selected.append({"skill": skill, "score": 0.85})
                    selected_names.add("error_handling_focus")
                    break

    # Keep max 6 skills (5 base + profile adjustments)
    selected.sort(key=lambda x: x["score"], reverse=True)
    return selected[:6]
