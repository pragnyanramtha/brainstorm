"""
Prompt assembler/optimizer — THE most important file in the system.
Takes all context and builds a perfect, self-contained single-shot prompt.
Uses Gemini Flash to assemble the prompt intelligently.
"""
import json
import traceback
from typing import Optional

from rich.console import Console

from backend.config import get_api_keys, ModelConfig

console = Console()


OPTIMIZER_SYSTEM_PROMPT = """You are a prompt engineering optimizer. Your SOLE job is to take raw context about a user's request and transform it into a PERFECT, self-contained, single-shot prompt that will be sent directly to an AI model.

You will receive:
1. The user's original message
2. An intent analysis (what they actually want)
3. Any clarification Q&A
4. The user's profile and preferences
5. Relevant memories about this user
6. Skills to apply (prompt engineering techniques)
7. Available tools
8. Project context

Your output must be a COMPLETE prompt — ready to send directly to the execution model. It should contain:

1. **Role & Expertise Assignment**: Start with "You are a senior [role]..." matching the task domain
2. **User Context**: Who this is for, their level, what they like/dislike
3. **Full Task Description**: Everything the model needs to know. INLINE everything — no references to "earlier conversation"
4. **Methodology**: Weave in the selected skills NATURALLY. Don't list them as bullet points — incorporate their techniques into the instructions
5. **Tool Instructions**: If tools are available, explain when and how to use them
6. **Constraints & Boundaries**: What to avoid, limits, user pet peeves
7. **Output Format**: Exactly how the response should be structured
8. **Quality Checklist**: Self-check criteria before responding

CRITICAL RULES:
- Output ONLY the prompt text. No meta-commentary. No "Here's your optimized prompt:". Just the prompt itself.
- The prompt must be SELF-CONTAINED. The execution model has ZERO context beyond what you write.
- Weave skills in naturally. Instead of "Apply chain_of_thought", write "Think through this step by step, showing your reasoning before the final answer."
- Match the user's preferences: if they want concise output, instruct the model to be brief. If they want detailed explanations, ask for thorough coverage.
- If the user has pet peeves (e.g., "don't use semicolons", "no emojis"), include those as explicit constraints.
- The prompt should feel like it was carefully hand-crafted by an expert prompt engineer, not auto-generated.
- For code tasks: always specify the language, framework, and any architectural patterns to follow.
- For writing tasks: specify the tone, audience, length, and format.
- Keep the prompt focused and actionable. Long doesn't mean better — but complete does.
- If project context exists, summarize what's been built so far so the model can continue coherently."""


async def build_optimized_prompt(
    user_message: str,
    intake_analysis: dict,
    clarification_qa: Optional[list] = None,
    user_profile: Optional[dict] = None,
    core_memories: Optional[list] = None,
    selected_skills: Optional[list] = None,
    available_tools: Optional[list] = None,
    project_context: Optional[str] = None,
    selected_approach: Optional[dict] = None,
) -> str:
    """
    Build a perfect single-shot prompt using Gemini Flash as the optimizer.
    In case of failure, falls back to a manually assembled prompt.
    """
    keys = get_api_keys()

    if not keys.gemini_api_key:
        return _fallback_prompt(user_message, intake_analysis, user_profile, selected_skills, project_context)

    # Build the meta-prompt (what we send to the optimizer model)
    context_sections = []

    # 1. Original message
    context_sections.append(f"=== USER'S ORIGINAL MESSAGE ===\n{user_message}")

    # 2. Intent analysis
    context_sections.append(
        f"=== INTENT ANALYSIS ===\n"
        f"Interpreted Intent: {intake_analysis.get('interpreted_intent', user_message)}\n"
        f"Task Type: {intake_analysis.get('task_type', 'conversation')}\n"
        f"Complexity: {intake_analysis.get('complexity', 3)}/10\n"
        f"Confidence: {intake_analysis.get('confidence_score', 90)}%"
    )

    # 3. Clarification Q&A
    if clarification_qa:
        qa_text = "\n".join(f"Q: {qa.get('question', '')}\nA: {qa.get('answer', '')}" for qa in clarification_qa)
        context_sections.append(f"=== CLARIFICATION Q&A ===\n{qa_text}")

    # 4. User profile
    if user_profile:
        profile_parts = [
            f"Technical Level: {user_profile.get('technical_level', 'unknown')}",
        ]
        if user_profile.get('domain'):
            profile_parts.append(f"Domain: {user_profile['domain']}")
        if user_profile.get('role'):
            profile_parts.append(f"Role: {user_profile['role']}")
        stack = user_profile.get('stack', [])
        if stack:
            profile_parts.append(f"Tech Stack: {', '.join(stack)}")
        prefs = user_profile.get('communication_preferences', {})
        if prefs:
            profile_parts.append(f"Prefers: {prefs.get('detail_level', 'balanced')} detail, {prefs.get('tone', 'friendly')} tone, {prefs.get('format', 'markdown')} format")
        pet_peeves = user_profile.get('pet_peeves', [])
        if pet_peeves:
            profile_parts.append(f"Pet Peeves (AVOID THESE): {', '.join(pet_peeves)}")
        positive = user_profile.get('positive_patterns', [])
        if positive:
            profile_parts.append(f"Things that work well: {', '.join(positive)}")

        context_sections.append(f"=== USER PROFILE ===\n" + "\n".join(profile_parts))

    # 5. Core memories
    if core_memories:
        memory_texts = []
        for m in core_memories[:15]:
            content = m.get('content', '') if isinstance(m, dict) else str(m)
            category = m.get('category', '') if isinstance(m, dict) else ''
            if content:
                memory_texts.append(f"[{category}] {content}" if category else content)
        if memory_texts:
            context_sections.append(f"=== RELEVANT MEMORIES ===\n" + "\n".join(f"- {m}" for m in memory_texts))

    # 6. Skills to apply
    if selected_skills:
        skills_text = []
        for skill in selected_skills:
            name = skill.get('name', '') if isinstance(skill, dict) else str(skill)
            template = skill.get('implementation_template', '') if isinstance(skill, dict) else ''
            if template:
                skills_text.append(f"SKILL '{name}': {template}")
            else:
                skills_text.append(f"SKILL: {name}")
        context_sections.append(f"=== SKILLS TO APPLY (weave these in naturally) ===\n" + "\n\n".join(skills_text))

    # 7. Available tools
    if available_tools:
        tools_text = json.dumps(available_tools, indent=2)
        context_sections.append(f"=== AVAILABLE TOOLS ===\n{tools_text}")

    # 8. Project context
    if project_context:
        context_sections.append(f"=== PROJECT CONTEXT (what's been built so far) ===\n{project_context}")

    # 9. Selected approach (from brainstorming)
    if selected_approach:
        approach_text = (
            f"Title: {selected_approach.get('title', '')}"
            f"\nDescription: {selected_approach.get('description', '')}"
            f"\nEffort Level: {selected_approach.get('effort_level', 'medium')}"
        )
        pros = selected_approach.get('pros', [])
        cons = selected_approach.get('cons', [])
        if pros:
            approach_text += f"\nStrengths: {', '.join(pros)}"
        if cons:
            approach_text += f"\nTradeoffs to manage: {', '.join(cons)}"
        context_sections.append(
            f"=== USER'S CHOSEN APPROACH (follow this direction) ===\n{approach_text}\n\n"
            f"IMPORTANT: The user specifically chose this approach after reviewing alternatives. "
            f"Implement according to this approach's philosophy and strengths. "
            f"Address the listed tradeoffs proactively."
        )

    # Target model info
    recommended = intake_analysis.get('recommended_model', 'gemini')
    context_sections.append(f"=== TARGET MODEL ===\nThis prompt will be sent to: {recommended}")

    full_meta_prompt = "\n\n".join(context_sections)

    try:
        from google import genai

        client = genai.Client(api_key=keys.gemini_api_key)

        response = client.models.generate_content(
            model=ModelConfig.OPTIMIZER_MODEL,
            contents=full_meta_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=OPTIMIZER_SYSTEM_PROMPT,
                temperature=0.4,
                max_output_tokens=4096,
            ),
        )

        optimized = response.text.strip()

        if not optimized or len(optimized) < 20:
            console.print("[yellow]Optimizer returned empty/short response, using fallback[/yellow]")
            return _fallback_prompt(user_message, intake_analysis, user_profile, selected_skills, project_context, selected_approach)

        return optimized

    except Exception as e:
        console.print(f"[red]Optimizer failed: {e}[/red]")
        console.print(traceback.format_exc())
        return _fallback_prompt(user_message, intake_analysis, user_profile, selected_skills, project_context, selected_approach)


def _fallback_prompt(
    user_message: str,
    intake_analysis: dict,
    user_profile: Optional[dict] = None,
    selected_skills: Optional[list] = None,
    project_context: Optional[str] = None,
    selected_approach: Optional[dict] = None,
) -> str:
    """Hand-crafted fallback prompt when the optimizer LLM fails."""
    parts = []

    # Role assignment
    task_type = intake_analysis.get('task_type', 'conversation')
    role_map = {
        'code': 'senior software engineer',
        'debugging': 'senior software engineer specializing in debugging',
        'system_design': 'senior systems architect',
        'writing': 'professional writer',
        'research': 'research analyst',
        'analysis': 'data analyst',
        'creative': 'creative director',
        'data': 'data scientist',
        'math': 'mathematician',
        'conversation': 'knowledgeable assistant',
    }
    role = role_map.get(task_type, 'knowledgeable assistant')
    parts.append(f"You are a {role} with 15+ years of experience.")

    # User context
    if user_profile:
        level = user_profile.get('technical_level', 'semi_technical')
        level_map = {
            'non_technical': 'The user is non-technical. Use plain language, explain concepts, avoid jargon.',
            'semi_technical': 'The user has some technical knowledge. Use standard terminology but explain complex concepts.',
            'technical': 'The user is technical. Use proper terminology, focus on implementation details.',
            'expert': 'The user is an expert. Be concise, use precise technical language, skip basics.',
        }
        parts.append(level_map.get(level, ''))

        stack = user_profile.get('stack', [])
        if stack:
            parts.append(f"Their tech stack includes: {', '.join(stack)}.")

        pet_peeves = user_profile.get('pet_peeves', [])
        if pet_peeves:
            parts.append(f"AVOID: {', '.join(pet_peeves)}.")

    # Task
    intent = intake_analysis.get('interpreted_intent', user_message)
    parts.append(f"\nTASK:\n{intent}")

    if project_context:
        parts.append(f"\nPROJECT CONTEXT:\n{project_context}")

    # Selected approach
    if selected_approach:
        parts.append(
            f"\nCHOSEN APPROACH: {selected_approach.get('title', '')}\n"
            f"{selected_approach.get('description', '')}\n"
            f"Follow this approach's philosophy and direction."
        )

    # Skills
    if selected_skills:
        skill_instructions = []
        for skill in selected_skills:
            template = skill.get('implementation_template', '') if isinstance(skill, dict) else ''
            if template:
                skill_instructions.append(template)
        if skill_instructions:
            parts.append("\nAPPROACH:\n" + "\n".join(f"- {s}" for s in skill_instructions))

    # Original message
    parts.append(f"\nUSER'S REQUEST:\n{user_message}")

    return "\n\n".join(parts)
