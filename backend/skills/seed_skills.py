"""
Seeds the database with 25 default skills on first run.
"""
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import Skill


SEED_SKILLS = [
    # --- Reasoning ---
    {
        "name": "chain_of_thought",
        "category": "reasoning",
        "description": "Think step by step, showing intermediate reasoning before the final answer",
        "implementation_template": (
            "Think through this step by step. Show your intermediate reasoning clearly before arriving at the final answer. "
            "Break complex logic into numbered steps. For each step, explain what you're doing and why. "
            "Don't jump to conclusions — walk through the reasoning chain explicitly."
        ),
        "best_for_task_types": json.dumps(["math", "analysis", "debugging", "code"]),
        "complexity_range_min": 3,
        "complexity_range_max": 10,
    },
    {
        "name": "tree_of_thought",
        "category": "reasoning",
        "description": "Explore 3 different approaches, evaluate pros/cons of each, then implement the best one",
        "implementation_template": (
            "Before implementing, explore at least 3 meaningfully different approaches to this problem. "
            "For each approach: (1) describe the approach, (2) list pros, (3) list cons, (4) estimate effort and risk. "
            "Then select the best approach based on your evaluation and implement it. "
            "Briefly justify why the chosen approach wins over alternatives."
        ),
        "best_for_task_types": json.dumps(["system_design", "creative", "analysis"]),
        "complexity_range_min": 6,
        "complexity_range_max": 10,
    },
    {
        "name": "self_consistency",
        "category": "reasoning",
        "description": "Solve the problem using 3 independent methods, verify the answers agree",
        "implementation_template": (
            "Solve this problem using at least 3 independent methods or perspectives. "
            "For each method, show the work and arrive at an answer independently. "
            "Then compare all answers. If they agree, present the answer with high confidence. "
            "If they disagree, analyze why and determine the most likely correct answer."
        ),
        "best_for_task_types": json.dumps(["math", "analysis"]),
        "complexity_range_min": 5,
        "complexity_range_max": 10,
    },
    {
        "name": "task_decomposition",
        "category": "reasoning",
        "description": "Break this into numbered subtasks, handle each one, then combine into final output",
        "implementation_template": (
            "Break this into clearly numbered subtasks. For each subtask: "
            "(1) state what needs to be done, (2) complete it, (3) verify it's correct. "
            "After all subtasks are complete, combine them into a cohesive final output. "
            "Ensure subtasks are ordered by dependency — complete prerequisites first."
        ),
        "best_for_task_types": json.dumps(["code", "system_design", "research"]),
        "complexity_range_min": 5,
        "complexity_range_max": 10,
    },
    {
        "name": "analogical_reasoning",
        "category": "reasoning",
        "description": "Relate this problem to a well-known solved problem, then adapt the solution",
        "implementation_template": (
            "Before solving, identify a well-known problem or pattern that's analogous to this one. "
            "Explain the analogy clearly: what maps to what? "
            "Then adapt the known solution to fit this specific problem, noting where the analogy breaks down "
            "and adjustments are needed."
        ),
        "best_for_task_types": json.dumps(["system_design", "debugging"]),
        "complexity_range_min": 4,
        "complexity_range_max": 8,
    },

    # --- Formatting ---
    {
        "name": "xml_structuring",
        "category": "formatting",
        "description": "Use XML tags to separate context, instructions, and constraints for Claude",
        "implementation_template": (
            "Structure your processing using clear XML-like sections: "
            "<context> for background information, <instructions> for what to do, "
            "<constraints> for limitations and rules, <output> for the final result. "
            "This helps organize complex tasks with multiple information types."
        ),
        "best_for_task_types": json.dumps(["code", "analysis", "research"]),
        "complexity_range_min": 1,
        "complexity_range_max": 10,
    },
    {
        "name": "structured_json_output",
        "category": "formatting",
        "description": "Return output as valid JSON matching a specified schema",
        "implementation_template": (
            "Return your output as valid, parseable JSON. Follow the specified schema exactly. "
            "Include all required fields. Use appropriate types (strings, numbers, arrays, objects). "
            "Do not include any text outside the JSON structure. Ensure the JSON is valid and complete."
        ),
        "best_for_task_types": json.dumps(["data", "code", "analysis"]),
        "complexity_range_min": 1,
        "complexity_range_max": 10,
    },
    {
        "name": "template_response",
        "category": "formatting",
        "description": "Provide an output skeleton with sections to fill in",
        "implementation_template": (
            "Structure your response using a clear template with labeled sections. "
            "Each section should have a descriptive heading. Fill in each section completely. "
            "Use consistent formatting throughout. Include transitions between sections."
        ),
        "best_for_task_types": json.dumps(["writing", "research", "analysis"]),
        "complexity_range_min": 1,
        "complexity_range_max": 7,
    },
    {
        "name": "markdown_formatting",
        "category": "formatting",
        "description": "Structure output with headers, bullet points, tables, and code blocks",
        "implementation_template": (
            "Format your response using rich markdown: use ## headers for sections, "
            "bullet points for lists, tables for comparisons, code blocks with language tags "
            "for code, bold for emphasis, and blockquotes for important notes. "
            "Make the output scannable and well-organized."
        ),
        "best_for_task_types": json.dumps(["writing", "research", "analysis", "code"]),
        "complexity_range_min": 1,
        "complexity_range_max": 10,
    },
    {
        "name": "component_architecture",
        "category": "formatting",
        "description": "Organize code output as separate, clearly labeled files/components",
        "implementation_template": (
            "Organize code into separate, clearly labeled files or components. "
            "Each file should have: a clear filename header, a brief comment explaining its purpose, "
            "and self-contained code that works with the other files. "
            "Show the file tree first, then each file's complete contents."
        ),
        "best_for_task_types": json.dumps(["code", "system_design"]),
        "complexity_range_min": 4,
        "complexity_range_max": 10,
    },

    # --- Quality ---
    {
        "name": "expert_persona",
        "category": "quality",
        "description": "Assign a specific expert role for domain-appropriate responses",
        "implementation_template": (
            "Approach this as a senior expert with 15+ years of experience in the relevant domain. "
            "Apply professional best practices, industry standards, and hard-won practical knowledge. "
            "Flag common pitfalls that less experienced practitioners would miss. "
            "Provide production-grade output, not textbook answers."
        ),
        "best_for_task_types": json.dumps(["code", "writing", "research", "analysis", "creative", "data", "math", "system_design", "debugging", "conversation"]),
        "complexity_range_min": 3,
        "complexity_range_max": 10,
    },
    {
        "name": "self_evaluation_rubric",
        "category": "quality",
        "description": "Score your output on accuracy, completeness, and clarity before finalizing",
        "implementation_template": (
            "Before finalizing your response, evaluate it against these criteria: "
            "Accuracy (1-5): Are all facts and code correct? "
            "Completeness (1-5): Does it fully address the request? "
            "Clarity (1-5): Is it easy to understand and use? "
            "If any score is below 4, revise that aspect before presenting the final output."
        ),
        "best_for_task_types": json.dumps(["code", "writing", "analysis", "research"]),
        "complexity_range_min": 4,
        "complexity_range_max": 10,
    },
    {
        "name": "negative_examples",
        "category": "quality",
        "description": "Avoid common bad patterns by knowing what NOT to produce",
        "implementation_template": (
            "Be aware of common anti-patterns for this type of task. "
            "Do NOT produce: generic filler text, vague non-answers, over-complicated solutions "
            "when simple ones work, copy-pasted boilerplate without customization, or solutions "
            "that ignore the specific context provided. Every part of your output should be purposeful."
        ),
        "best_for_task_types": json.dumps(["writing", "creative", "code"]),
        "complexity_range_min": 3,
        "complexity_range_max": 8,
    },
    {
        "name": "constraint_checklist",
        "category": "quality",
        "description": "Include an explicit checklist of requirements and verify each is met",
        "implementation_template": (
            "Before responding, extract all explicit and implicit requirements from the request. "
            "Create a mental checklist. After completing your response, verify each requirement is met. "
            "If any requirement is missing, add it. Include a brief verification section showing "
            "that all constraints have been satisfied."
        ),
        "best_for_task_types": json.dumps(["code", "system_design"]),
        "complexity_range_min": 4,
        "complexity_range_max": 10,
    },
    {
        "name": "audience_calibration",
        "category": "quality",
        "description": "Adjust language, depth, and assumptions based on the audience",
        "implementation_template": (
            "Calibrate your response to the user's expertise level: "
            "For beginners: explain concepts, avoid jargon, provide examples. "
            "For intermediate: use standard terminology, focus on practical application. "
            "For experts: be concise, focus on nuances, skip basics, use precise technical language. "
            "Match the user's communication style and expectations."
        ),
        "best_for_task_types": json.dumps(["writing", "research", "creative"]),
        "complexity_range_min": 1,
        "complexity_range_max": 10,
    },

    # --- Domain: Code ---
    {
        "name": "security_review",
        "category": "domain",
        "description": "Review for security vulnerabilities: injection, XSS, auth bypass, secrets exposure, CSRF",
        "implementation_template": (
            "Review all code for security vulnerabilities: "
            "1. Input validation — are all inputs sanitized? "
            "2. Injection — SQL, command, template injection risks? "
            "3. Authentication/Authorization — proper checks on all endpoints? "
            "4. Secrets — any hardcoded keys, passwords, tokens? "
            "5. XSS — is user-generated content properly escaped? "
            "6. CSRF — are state-changing operations protected? "
            "Flag any issues with severity (critical/high/medium/low) and remediation."
        ),
        "best_for_task_types": json.dumps(["code", "debugging"]),
        "complexity_range_min": 5,
        "complexity_range_max": 10,
    },
    {
        "name": "error_handling_focus",
        "category": "domain",
        "description": "Include comprehensive error handling, edge cases, input validation, and meaningful error messages",
        "implementation_template": (
            "Implement robust error handling: "
            "1. Validate all inputs at entry points "
            "2. Handle expected failure modes (network, file, auth, parsing errors) "
            "3. Use specific exception types, not bare except "
            "4. Provide meaningful error messages that help users fix the problem "
            "5. Consider edge cases: empty inputs, null values, boundary conditions "
            "6. Fail gracefully — degrade functionality rather than crash"
        ),
        "best_for_task_types": json.dumps(["code"]),
        "complexity_range_min": 3,
        "complexity_range_max": 10,
    },
    {
        "name": "test_generation",
        "category": "domain",
        "description": "Generate unit tests covering happy path, edge cases, and error cases",
        "implementation_template": (
            "Generate comprehensive tests: "
            "1. Happy path — does it work correctly with valid inputs? "
            "2. Edge cases — empty strings, zero, max values, special characters "
            "3. Error cases — invalid inputs, missing data, permission errors "
            "4. Use descriptive test names that explain what's being tested "
            "5. Follow Arrange-Act-Assert pattern "
            "6. Mock external dependencies "
            "Aim for meaningful coverage, not just line coverage."
        ),
        "best_for_task_types": json.dumps(["code"]),
        "complexity_range_min": 4,
        "complexity_range_max": 10,
    },
    {
        "name": "performance_awareness",
        "category": "domain",
        "description": "Consider time/space complexity, identify bottlenecks, suggest optimizations",
        "implementation_template": (
            "Consider performance implications: "
            "1. State the time and space complexity of your solution "
            "2. Identify potential bottlenecks (N+1 queries, unnecessary loops, memory allocation) "
            "3. Suggest optimizations if performance is critical "
            "4. Consider: caching, lazy loading, pagination, connection pooling "
            "5. Don't prematurely optimize — note where optimization would matter at scale"
        ),
        "best_for_task_types": json.dumps(["code", "system_design"]),
        "complexity_range_min": 5,
        "complexity_range_max": 10,
    },
    {
        "name": "code_review_lens",
        "category": "domain",
        "description": "Review code for readability, maintainability, DRY violations, naming, architecture",
        "implementation_template": (
            "Review through these lenses: "
            "1. Readability — can someone understand this in 30 seconds? "
            "2. Naming — are variables, functions, classes named clearly and consistently? "
            "3. DRY — is there duplicated logic that should be extracted? "
            "4. Single Responsibility — does each function/class do one thing well? "
            "5. Dependencies — are they minimal and well-managed? "
            "6. Architecture — does the structure support future changes?"
        ),
        "best_for_task_types": json.dumps(["code", "debugging"]),
        "complexity_range_min": 3,
        "complexity_range_max": 10,
    },

    # --- Domain: General ---
    {
        "name": "research_methodology",
        "category": "domain",
        "description": "Structure research as: question → methodology → findings → analysis → limitations → conclusion",
        "implementation_template": (
            "Structure research systematically: "
            "1. Research Question — clearly state what you're investigating "
            "2. Methodology — how will you approach this? What sources? "
            "3. Findings — present discovered information objectively "
            "4. Analysis — interpret the findings, identify patterns "
            "5. Limitations — what couldn't you cover? What might be biased? "
            "6. Conclusion — synthesize into actionable insights"
        ),
        "best_for_task_types": json.dumps(["research"]),
        "complexity_range_min": 4,
        "complexity_range_max": 10,
    },
    {
        "name": "business_analysis",
        "category": "domain",
        "description": "Frame analysis with: problem statement → impact → options → recommendation → ROI → risks",
        "implementation_template": (
            "Frame the analysis as a business case: "
            "1. Problem Statement — what's the core issue? "
            "2. Impact — who's affected and how much? Quantify where possible "
            "3. Options — present 2-3 viable paths forward "
            "4. Recommendation — which option and why? "
            "5. Expected ROI — what's the return? Timeline? "
            "6. Risks — what could go wrong? Mitigation strategies?"
        ),
        "best_for_task_types": json.dumps(["analysis"]),
        "complexity_range_min": 4,
        "complexity_range_max": 10,
    },
    {
        "name": "creative_constraints",
        "category": "domain",
        "description": "Apply creative writing techniques: show don't tell, specific details, active voice",
        "implementation_template": (
            "Apply creative writing best practices: "
            "1. Show, don't tell — use specific examples and scenarios "
            "2. Specific details over generalities — 'reduced load time by 40%' not 'improved performance' "
            "3. Active voice — 'the system processes' not 'the data is processed by' "
            "4. Sensory and concrete language — make abstract concepts tangible "
            "5. Hook the reader — lead with the most interesting or important point"
        ),
        "best_for_task_types": json.dumps(["creative", "writing"]),
        "complexity_range_min": 3,
        "complexity_range_max": 8,
    },
    {
        "name": "data_analysis_pipeline",
        "category": "domain",
        "description": "Structure as: hypothesis → data exploration → methodology → visualization plan → findings → insights",
        "implementation_template": (
            "Follow a data analysis pipeline: "
            "1. Hypothesis — what do you expect to find? Why? "
            "2. Data Exploration — describe the data, its shape, quality, gaps "
            "3. Methodology — what statistical/analytical methods will you use? "
            "4. Visualization Plan — what charts/graphs best communicate findings? "
            "5. Findings — present results with supporting data "
            "6. Actionable Insights — so what? What should the user DO with this information?"
        ),
        "best_for_task_types": json.dumps(["data", "analysis"]),
        "complexity_range_min": 5,
        "complexity_range_max": 10,
    },
    {
        "name": "concise_mode",
        "category": "quality",
        "description": "Be direct and brief. No preamble, no caveats. Answer first, explain only if asked.",
        "implementation_template": (
            "Be direct and concise: "
            "- Lead with the answer or solution, not context "
            "- No 'Great question!' or 'I'd be happy to help' "
            "- No disclaimers or caveats unless they materially affect the answer "
            "- If code is requested, provide code first, explanation second "
            "- Use short sentences. Every word should earn its place."
        ),
        "best_for_task_types": json.dumps(["code", "writing", "research", "analysis", "creative", "data", "math", "system_design", "debugging", "conversation"]),
        "complexity_range_min": 1,
        "complexity_range_max": 10,
    },
]


async def seed_skills(session: AsyncSession):
    """Seed skills table if empty."""
    result = await session.execute(select(Skill).limit(1))
    if result.scalars().first() is not None:
        return  # Already seeded

    for skill_data in SEED_SKILLS:
        skill = Skill(**skill_data)
        session.add(skill)

    await session.commit()
