"""
Intent parser + ambiguity scorer.
Uses Gemini Flash to analyze user messages and determine intent, task type, complexity, and confidence.
"""
import json
import traceback
from typing import Optional

from pydantic import BaseModel
from rich.console import Console

from backend.config import get_api_keys, ModelConfig

console = Console()

VALID_TASK_TYPES = [
    "code", "writing", "research", "analysis", "creative",
    "data", "math", "system_design", "debugging", "conversation",
]


class IntakeAnalysis(BaseModel):
    interpreted_intent: str
    task_type: str
    complexity: int
    confidence_score: int
    ambiguity_areas: list[str]
    inferred_context: dict
    suggested_capabilities: list[str]
    recommended_model: str


INTAKE_SYSTEM_PROMPT = """You are an intent analysis engine for an AI middleware system called Middle Manager AI.
Your job is to deeply analyze a user's message and determine what they ACTUALLY want — not just what they literally said.

You must return a JSON object with these exact fields:

{
  "interpreted_intent": "A single clear sentence describing what the user truly wants to accomplish",
  "task_type": "one of: code, writing, research, analysis, creative, data, math, system_design, debugging, conversation",
  "complexity": <integer 1-10>,
  "confidence_score": <integer 0-100>,
  "ambiguity_areas": ["list of specific things that are unclear or could be interpreted multiple ways"],
  "inferred_context": {"key": "value pairs of things you can reasonably infer from context"},
  "suggested_capabilities": ["list of tools/capabilities this task would benefit from, e.g. 'web_search', 'file_write', 'code_execution'"],
  "recommended_model": "gemini or claude"
}

CRITICAL RULES:
1. Parse TRUE INTENT, not literal words. "Make me a website" means they want HTML/CSS/JS code, not a lecture about web development.
2. Be AGGRESSIVE about finding ambiguity. If a request could mean 2+ things, list ALL ambiguity areas.
3. Score confidence CONSERVATIVELY:
   - 95-100: Crystal clear, single possible interpretation, all context available
   - 80-94: Mostly clear, but minor details could vary
   - 60-79: Significant ambiguity — multiple interpretations possible
   - 40-59: Very ambiguous — need clarification on core intent
   - 0-39: Almost no idea what they want
4. Use the user profile to INFER what you can. If their profile says "React developer" and they say "build a component", you can infer React. Don't mark that as ambiguous.
5. If the user profile answers a potential ambiguity, DON'T list it as ambiguous. Use inferred_context instead.
6. Complexity scoring:
   - 1-2: Trivial (explain a concept, simple question)
   - 3-4: Easy (simple function, short writing)
   - 5-6: Medium (multi-file code, research with analysis)
   - 7-8: Hard (system design, complex debugging, full application)
   - 9-10: Expert (novel algorithms, complex architecture, multi-domain integration)
7. Model recommendation:
   - "claude" for: code, debugging, system_design, math (if Claude key is available)
   - "gemini" for: writing, research, analysis, creative, data, conversation
   - When in doubt, recommend "gemini"

EXAMPLES:

User: "help me sort a list"
Analysis: Low confidence (65). Ambiguity: what language? what kind of list? sorting criteria? in-place or new list?

User (profile: Python developer): "help me sort a list"
Analysis: Higher confidence (78). Infer Python from profile. Still ambiguous: sorting criteria, in-place vs new.

User: "Build me a REST API for a todo app with authentication"
Analysis: High confidence (88). Clear intent. Infer their stack from profile. Complexity 6-7.

User: "fix this"
Analysis: Very low confidence (20). No code provided, no context about what's broken.

RESPOND WITH ONLY THE JSON OBJECT. No markdown, no explanation, no backticks."""


async def analyze_intent(
    user_message: str,
    user_profile: Optional[dict] = None,
    core_memories: Optional[list] = None,
    project_context: Optional[str] = None,
) -> IntakeAnalysis:
    """
    Analyze user intent using Gemini Flash.
    Returns structured IntakeAnalysis with confidence scoring.
    """
    keys = get_api_keys()

    # Build context for the analysis
    context_parts = []

    if user_profile:
        context_parts.append(f"USER PROFILE:\n- Technical Level: {user_profile.get('technical_level', 'unknown')}")
        if user_profile.get('domain'):
            context_parts.append(f"- Domain: {user_profile['domain']}")
        if user_profile.get('role'):
            context_parts.append(f"- Role: {user_profile['role']}")
        stack = user_profile.get('stack', [])
        if stack:
            context_parts.append(f"- Tech Stack: {', '.join(stack)}")
        prefs = user_profile.get('communication_preferences', {})
        if prefs:
            context_parts.append(f"- Communication Preferences: {json.dumps(prefs)}")

    if core_memories:
        memory_texts = [m.get('content', '') if isinstance(m, dict) else str(m) for m in core_memories[:10]]
        if memory_texts:
            context_parts.append(f"RELEVANT MEMORIES ABOUT THIS USER:\n" + "\n".join(f"- {m}" for m in memory_texts))

    if project_context:
        context_parts.append(f"CURRENT PROJECT CONTEXT:\n{project_context}")

    # Note whether Claude is available
    claude_available = bool(keys.anthropic_api_key)
    context_parts.append(f"AVAILABLE MODELS: Gemini (always available), Claude ({'available' if claude_available else 'NOT available'})")

    full_context = "\n\n".join(context_parts) if context_parts else "No user profile or context available."

    user_prompt = f"{full_context}\n\n---\n\nUSER MESSAGE:\n{user_message}"

    try:
        from google import genai

        client = genai.Client(api_key=keys.gemini_api_key)

        response = client.models.generate_content(
            model=ModelConfig.INTAKE_MODEL,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=INTAKE_SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        response_text = response.text.strip()

        # Parse the JSON response
        data = json.loads(response_text)

        # Validate and clamp values
        task_type = data.get("task_type", "conversation")
        if task_type not in VALID_TASK_TYPES:
            task_type = "conversation"

        complexity = max(1, min(10, int(data.get("complexity", 3))))
        confidence = max(0, min(100, int(data.get("confidence_score", 50))))

        recommended = data.get("recommended_model", "gemini")
        if recommended not in ("gemini", "claude"):
            recommended = "gemini"
        if recommended == "claude" and not claude_available:
            recommended = "gemini"

        return IntakeAnalysis(
            interpreted_intent=data.get("interpreted_intent", user_message),
            task_type=task_type,
            complexity=complexity,
            confidence_score=confidence,
            ambiguity_areas=data.get("ambiguity_areas", []),
            inferred_context=data.get("inferred_context", {}),
            suggested_capabilities=data.get("suggested_capabilities", []),
            recommended_model=recommended,
        )

    except Exception as e:
        console.print(f"[red]Intake analysis failed: {e}[/red]")
        console.print(traceback.format_exc())

        # Fallback: basic heuristic analysis
        return _fallback_analysis(user_message, claude_available)


def _fallback_analysis(user_message: str, claude_available: bool) -> IntakeAnalysis:
    """Heuristic fallback when LLM intake fails."""
    msg_lower = user_message.lower()

    # Simple task type detection
    code_keywords = ["code", "function", "class", "api", "build", "implement", "fix", "bug", "error", "debug", "refactor"]
    writing_keywords = ["write", "essay", "article", "blog", "email", "letter"]
    research_keywords = ["research", "find", "search", "what is", "how does", "explain"]
    analysis_keywords = ["analyze", "compare", "evaluate", "review"]
    creative_keywords = ["design", "creative", "story", "poem"]
    data_keywords = ["data", "csv", "chart", "graph", "statistics"]
    math_keywords = ["calculate", "math", "formula", "equation", "solve"]

    task_type = "conversation"
    recommended = "gemini"

    for keywords, ttype in [
        (code_keywords, "code"),
        (writing_keywords, "writing"),
        (research_keywords, "research"),
        (analysis_keywords, "analysis"),
        (creative_keywords, "creative"),
        (data_keywords, "data"),
        (math_keywords, "math"),
    ]:
        if any(kw in msg_lower for kw in keywords):
            task_type = ttype
            break

    if task_type in ("code", "debugging", "system_design", "math") and claude_available:
        recommended = "claude"

    word_count = len(user_message.split())
    complexity = min(10, max(1, word_count // 10 + 2))

    return IntakeAnalysis(
        interpreted_intent=user_message[:200],
        task_type=task_type,
        complexity=complexity,
        confidence_score=60,
        ambiguity_areas=["Could not perform full intent analysis — using heuristic fallback"],
        inferred_context={},
        suggested_capabilities=[],
        recommended_model=recommended,
    )
