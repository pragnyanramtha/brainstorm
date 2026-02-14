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


class ApproachProposal(BaseModel):
    id: str  # "a", "b", "c"
    title: str
    description: str
    pros: list[str] = []
    cons: list[str] = []
    effort_level: str = "medium"  # low | medium | high
    recommended: bool = False


class ApproachProposalResult(BaseModel):
    approaches: list[ApproachProposal]
    context_summary: str = ""


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


APPROACH_PROPOSER_SYSTEM_PROMPT = """You are a design strategist for an AI middleware system. After a user has answered clarifying questions about their project, your job is to propose 2-3 meaningfully different approaches they could take.

You will receive:
1. The user's original message
2. An intent analysis
3. The clarification Q&A (questions the user already answered)
4. The user's profile

You must return a JSON object:
{
  "context_summary": "A 1-2 sentence summary of what the user wants, incorporating their clarification answers",
  "approaches": [
    {
      "id": "a",
      "title": "Short approach name (3-6 words)",
      "description": "2-3 sentence description of what this approach entails and why someone would choose it",
      "pros": ["Advantage 1", "Advantage 2", "Advantage 3"],
      "cons": ["Tradeoff 1", "Tradeoff 2"],
      "effort_level": "low | medium | high",
      "recommended": true/false
    }
  ]
}

CRITICAL RULES:
1. Exactly 2-3 approaches. No more, no less.
2. Approaches must be MEANINGFULLY DIFFERENT — not just variations of the same thing.
   - BAD: "React with Tailwind" vs "React with CSS Modules" (too similar)
   - GOOD: "Minimalist single-page" vs "Full marketing site with CMS" vs "Interactive demo-first design"
3. Mark exactly ONE approach as recommended. Choose based on the user's profile and answers.
4. Each approach should have 2-3 pros and 1-2 cons. Be honest about tradeoffs.
5. Effort levels should be realistic: low (hours), medium (1-2 days), high (3+ days).
6. Titles should be catchy and descriptive — users will scan these quickly.
7. Descriptions should explain WHY someone would choose this approach, not just WHAT it includes.
8. CALIBRATE to the user's technical level. For non-technical users, avoid jargon in descriptions.
9. Incorporate the user's clarification answers into the approaches. If they said "dark theme", all approaches should use dark theme — the differentiation should be on ARCHITECTURE and STRATEGY, not on preferences they already stated.

EXAMPLES:

For "create a landing page" (user answered: SaaS product, target developers, wants sign-up conversion):
- Approach A: "Developer-First Technical Landing" — Code examples front and center, terminal-style hero, GitHub-style design. Speaks directly to developers in their language.
- Approach B: "Conversion-Optimized Marketing Page" — Classic SaaS layout: hero, features, social proof, pricing, CTA. Proven conversion patterns with A/B testable sections.
- Approach C: "Interactive Product Demo" — Let the product sell itself. Embedded live demo as the hero, minimal marketing copy, immediate hands-on experience.

For "build a REST API" (user answered: e-commerce, needs auth + payments):
- Approach A: "Monolith with Batteries" — Single FastAPI app with everything built-in. Fastest to ship, easiest to debug.
- Approach B: "Modular Service Architecture" — Separate auth, products, orders, payments modules. Clean boundaries, ready for future scaling.

RESPOND WITH ONLY THE JSON OBJECT. No markdown, no explanation."""


async def generate_approach_proposals(
    intake_analysis: dict,
    user_message: str,
    clarification_qa: dict,
    user_profile: Optional[dict] = None,
) -> ApproachProposalResult:
    """
    Generate 2-3 approach proposals after clarification questions have been answered.
    """
    keys = get_api_keys()

    if not keys.gemini_api_key:
        return ApproachProposalResult(approaches=[], context_summary="")

    context_parts = [f"USER'S ORIGINAL MESSAGE:\n{user_message}"]

    context_parts.append(
        f"\nINTENT ANALYSIS:\n"
        f"- Interpreted Intent: {intake_analysis.get('interpreted_intent', '')}\n"
        f"- Task Type: {intake_analysis.get('task_type', '')}\n"
        f"- Complexity: {intake_analysis.get('complexity', '')}/10"
    )

    if clarification_qa:
        qa_text = "\n".join(f"Q: {q}\nA: {a}" for q, a in clarification_qa.items())
        context_parts.append(f"\nCLARIFICATION Q&A (user already answered these):\n{qa_text}")

    if user_profile:
        context_parts.append(
            f"\nUSER PROFILE:\n"
            f"- Technical Level: {user_profile.get('technical_level', 'unknown')}\n"
            f"- Domain: {user_profile.get('domain', 'not specified')}\n"
            f"- Role: {user_profile.get('role', 'not specified')}\n"
            f"- Stack: {json.dumps(user_profile.get('stack', []))}"
        )

    full_prompt = "\n".join(context_parts)

    try:
        from google import genai

        client = genai.Client(api_key=keys.gemini_api_key)

        response = client.models.generate_content(
            model=ModelConfig.CLARIFIER_MODEL,
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=APPROACH_PROPOSER_SYSTEM_PROMPT,
                temperature=0.5,
                response_mime_type="application/json",
            ),
        )

        response_text = response.text.strip()
        data = json.loads(response_text)

        approaches = []
        for a_data in data.get("approaches", [])[:3]:
            approaches.append(ApproachProposal(
                id=a_data.get("id", str(len(approaches))),
                title=a_data.get("title", ""),
                description=a_data.get("description", ""),
                pros=a_data.get("pros", []),
                cons=a_data.get("cons", []),
                effort_level=a_data.get("effort_level", "medium"),
                recommended=a_data.get("recommended", False),
            ))

        return ApproachProposalResult(
            approaches=approaches,
            context_summary=data.get("context_summary", ""),
        )

    except Exception as e:
        console.print(f"[red]Approach proposal generation failed: {e}[/red]")
        console.print(traceback.format_exc())
        return ApproachProposalResult(approaches=[], context_summary="")
