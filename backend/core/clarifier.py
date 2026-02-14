"""
Clarifying question generator.
Uses Gemini Flash to generate smart, contextual questions when user intent is ambiguous.
"""
import json
import traceback
from typing import Optional

from pydantic import BaseModel
from rich.console import Console

from backend.config import get_api_keys, ModelConfig

console = Console()


class ClarificationQuestion(BaseModel):
    question: str
    question_type: str  # multiple_choice | yes_no | free_text
    options: list[str] = []
    default: str = ""
    why_it_matters: str = ""


class ClarificationResult(BaseModel):
    questions: list[ClarificationQuestion]
    needs_clarification: bool


CLARIFIER_SYSTEM_PROMPT = """You are a clarification specialist for an AI middleware system. Your job is to generate smart, precise clarifying questions when a user's request is ambiguous.

You will receive:
1. The user's original message
2. An intent analysis showing what's ambiguous
3. The user's profile (technical level, domain, preferences)

You must return a JSON object:
{
  "questions": [
    {
      "question": "The question text, calibrated to the user's technical level",
      "question_type": "multiple_choice | yes_no | free_text",
      "options": ["Option A", "Option B", "Option C"],
      "default": "The best default if user skips",
      "why_it_matters": "Brief explanation of why this choice matters (shown as helper text)"
    }
  ]
}

CRITICAL RULES:
1. Maximum 4 questions. Fewer is better. Only ask what genuinely matters.
2. PREFER multiple_choice — give the user easy options to click, not blanks to fill.
3. ALWAYS provide a default for every question. The default should be the most likely/common answer.
4. NEVER ask what the profile already tells you. If they're a React developer, don't ask "what framework?"
5. NEVER ask vague questions like:
   - "Can you tell me more?"
   - "What do you mean by...?"
   - "Could you elaborate?"
6. ORDER by impact — most important question first.
7. CALIBRATE language to user's technical level:
   - non_technical: Plain English, no jargon, explain implications
   - semi_technical: Some jargon OK, brief explanations
   - technical: Use proper terminology, skip obvious explanations
   - expert: Be concise, use precise technical terms
8. Each question should resolve a SPECIFIC ambiguity from the analysis.
9. For yes/no questions, always use question_type "yes_no" (renders as toggle buttons).
10. Make questions feel conversational, not like a form.

EXAMPLES:

For "build me a website" from a semi-technical user:
- "What kind of website? (multiple_choice: Personal portfolio, Business/landing page, E-commerce store, Blog, Web application)" — default: "Personal portfolio"
- "Should it have a backend/database, or just static pages? (yes_no)" — default: "No"

For "fix this error" from a technical user (with error message provided):
- "Should I just fix the immediate error, or also refactor the surrounding code for robustness? (multiple_choice: Just fix the error, Fix and add error handling, Full refactor of this section)" — default: "Fix and add error handling"

RESPOND WITH ONLY THE JSON OBJECT. No markdown, no explanation."""


async def generate_clarifications(
    intake_analysis: dict,
    user_message: str,
    user_profile: Optional[dict] = None,
    core_memories: Optional[list] = None,
) -> ClarificationResult:
    """
    Generate clarifying questions based on intake analysis.
    Only called when confidence < 85.
    """
    keys = get_api_keys()

    if not keys.gemini_api_key:
        return ClarificationResult(questions=[], needs_clarification=False)

    # Build the prompt
    context_parts = [f"USER'S ORIGINAL MESSAGE:\n{user_message}"]

    context_parts.append(f"\nINTENT ANALYSIS:\n"
        f"- Interpreted Intent: {intake_analysis.get('interpreted_intent', '')}\n"
        f"- Task Type: {intake_analysis.get('task_type', '')}\n"
        f"- Complexity: {intake_analysis.get('complexity', '')}/10\n"
        f"- Confidence: {intake_analysis.get('confidence_score', '')}%\n"
        f"- Ambiguity Areas: {json.dumps(intake_analysis.get('ambiguity_areas', []))}\n"
        f"- Inferred Context: {json.dumps(intake_analysis.get('inferred_context', {}))}")

    if user_profile:
        context_parts.append(f"\nUSER PROFILE:\n"
            f"- Technical Level: {user_profile.get('technical_level', 'unknown')}\n"
            f"- Domain: {user_profile.get('domain', 'not specified')}\n"
            f"- Role: {user_profile.get('role', 'not specified')}\n"
            f"- Stack: {json.dumps(user_profile.get('stack', []))}\n"
            f"- Preferences: {json.dumps(user_profile.get('communication_preferences', {}))}")

    if core_memories:
        memory_texts = [m.get('content', '') if isinstance(m, dict) else str(m) for m in core_memories[:5]]
        if memory_texts:
            context_parts.append(f"\nRELEVANT MEMORIES:\n" + "\n".join(f"- {m}" for m in memory_texts))

    full_prompt = "\n".join(context_parts)

    try:
        from google import genai

        client = genai.Client(api_key=keys.gemini_api_key)

        response = client.models.generate_content(
            model=ModelConfig.CLARIFIER_MODEL,
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=CLARIFIER_SYSTEM_PROMPT,
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )

        response_text = response.text.strip()
        data = json.loads(response_text)

        questions = []
        for q_data in data.get("questions", [])[:4]:  # Max 4 questions
            q_type = q_data.get("question_type", "free_text")
            if q_type not in ("multiple_choice", "yes_no", "free_text"):
                q_type = "free_text"

            questions.append(ClarificationQuestion(
                question=q_data.get("question", ""),
                question_type=q_type,
                options=q_data.get("options", []),
                default=q_data.get("default", ""),
                why_it_matters=q_data.get("why_it_matters", ""),
            ))

        return ClarificationResult(
            questions=questions,
            needs_clarification=len(questions) > 0,
        )

    except Exception as e:
        console.print(f"[red]Clarification generation failed: {e}[/red]")
        console.print(traceback.format_exc())
        return ClarificationResult(questions=[], needs_clarification=False)
