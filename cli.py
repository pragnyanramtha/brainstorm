#!/usr/bin/env python3
"""
Brainstorm CLI — interactive coding assistant that builds optimized prompts,
asks clarifying questions in a loop until confident, then hands off to Gemini CLI.

Flow:
1. Who are you? (name, role, tech level, stack)
2. What do you want to build?
3. Analyze intent -> if confidence < threshold, ask clarifying questions
4. Re-analyze with answers -> loop until confidence >= threshold
5. Propose approaches (pick one)
6. Select skills + MCPs based on task
7. Discover & install agent skills from SkillKit marketplace (15,000+ skills)
8. Build full prompt with skills baked in
9. Hand off to Gemini CLI in ~/dev/<project-name>

SkillKit Integration:
- Searches 15,000+ community skills from Anthropic, Vercel, Expo, Supabase, etc.
- Installs relevant skills for your task (testing, security, React, TypeScript, etc.)
- Skills are made available to the AI agent during execution
"""
import json
import os
import re
import subprocess
import sys
import shutil
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.rule import Rule
from rich.markdown import Markdown
import questionary
from questionary import Style, Choice

# ── Load .env ──
ENV_PATH = Path(__file__).parent / ".env"
WORKSPACE_ENV = Path(__file__).parent / "workspace" / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
if WORKSPACE_ENV.exists():
    load_dotenv(WORKSPACE_ENV, override=False)

console = Console()

# ── Bash shell detection ──
def get_bash_executable() -> str:
    """Get bash executable path, preferring Git Bash on Windows."""
    if sys.platform == "win32":
        # Try common Git Bash locations
        bash_paths = [
            "C:\\Program Files\\Git\\bin\\bash.exe",
            "C:\\Program Files (x86)\\Git\\bin\\bash.exe",
            os.path.expanduser("~\\scoop\\apps\\git\\current\\bin\\bash.exe"),
            os.path.expanduser("~\\scoop\\apps\\git\\current\\usr\\bin\\bash.exe"),
        ]
        for path in bash_paths:
            if os.path.exists(path):
                # Return path in short (8.3) format to avoid space issues
                try:
                    import ctypes
                    from ctypes import wintypes
                    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
                    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
                    _GetShortPathNameW.restype = wintypes.DWORD
                    
                    output_buf_size = 0
                    while True:
                        output_buf = ctypes.create_unicode_buffer(output_buf_size)
                        needed = _GetShortPathNameW(path, output_buf, output_buf_size)
                        if output_buf_size >= needed:
                            return output_buf.value
                        else:
                            output_buf_size = needed
                except Exception:
                    # Fallback: just return the path as-is
                    return path
        # Try to find bash in PATH
        bash = shutil.which("bash")
        if bash:
            return bash
        # Fallback: assume bash is available (WSL or Git Bash in PATH)
        return "bash"
    else:
        return "/bin/bash"

BASH_EXECUTABLE = get_bash_executable()

# ── Styling ──
S = Style([
    ("qmark", "fg:#7c3aed bold"),
    ("question", "fg:#e2e8f0 bold"),
    ("answer", "fg:#22d3ee bold"),
    ("pointer", "fg:#7c3aed bold"),
    ("highlighted", "fg:#22d3ee bold"),
    ("selected", "fg:#22d3ee"),
    ("separator", "fg:#4b5563"),
    ("instruction", "fg:#9ca3af"),
    ("text", "fg:#d1d5db"),
])
PROMPT_STYLE = S  # Alias for compatibility

# ── Models ──
FAST_MODEL = "gemini-3-flash-preview"
EXEC_MODEL = "gemini-3-flash-preview"
CONFIDENCE_THRESHOLD = 88
MAX_CLARIFICATION_ROUNDS = 4

# Model aliases for compatibility
CLARIFIER_MODEL = FAST_MODEL
GEMINI_MODEL = EXEC_MODEL

# ── Dev directory ──
DEV_DIR = Path.home() / "dev"
DEV_DIR.mkdir(parents=True, exist_ok=True)


def get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        console.print("[red]No GEMINI_API_KEY found in .env[/red]")
        console.print(f"Add it to: {ENV_PATH}")
        sys.exit(1)
    return key


def header():
    console.print()
    t = Text()
    t.append("BRAINSTORM", style="bold #7c3aed")
    t.append(" CLI", style="bold #22d3ee")
    console.print(Panel(t, subtitle="coding assistant", border_style="#4b5563", padding=(0, 2)))
    console.print()


def ask_who_you_are() -> dict:
    console.print(Rule("[bold #7c3aed]Who are you?[/]", style="#4b5563"))
    console.print()

    name = questionary.text("Your name:", style=S).ask() or "Builder"

    role = questionary.select(
        "Your role:",
        choices=["Full-stack developer", "Frontend developer", "Backend developer",
                 "Designer", "Product manager", "Student / Learning"],
        style=S,
    ).ask() or "Developer"

    level = questionary.select(
        "Technical level:",
        choices=[
            Choice("Expert -- skip the basics", value="expert"),
            Choice("Technical -- comfortable with code", value="technical"),
            Choice("Semi-technical -- know some coding", value="semi_technical"),
            Choice("Non-technical -- explain everything", value="non_technical"),
        ],
        style=S,
    ).ask() or "semi_technical"

    stack = questionary.checkbox(
        "Tech stack (space to select, enter to confirm):",
        choices=["React", "Next.js", "Vue", "Svelte", "Angular",
                 "Node.js", "Python", "Go", "Rust", "Java",
                 "TypeScript", "Tailwind CSS", "PostgreSQL", "MongoDB",
                 "Docker", "AWS", "Vercel"],
        style=S,
    ).ask() or []

    console.print()
    return {"name": name, "role": role, "technical_level": level, "stack": stack}


# ──────────────────────────────────────────────
# Step 2: What to build
# ──────────────────────────────────────────────

def ask_what_to_build() -> str:
    """Ask the user what they want to build."""
    console.print(Rule("[bold #7c3aed]What do you want to build?[/]", style="#4b5563"))
    console.print()
    console.print("[#9ca3af]Describe your project. Be as detailed or vague as you want —[/]")
    console.print("[#9ca3af]we'll ask follow-up questions to fill in the gaps.[/]")
    console.print()

    message = questionary.text(
        "Describe your project:",
        multiline=True,
        style=PROMPT_STYLE,
        instruction="(press ESC then Enter to submit)",
    ).ask()

    if not message or not message.strip():
        console.print("[red]No project description provided. Exiting.[/red]")
        sys.exit(1)

    console.print()
    return message.strip()


# ──────────────────────────────────────────────
# Gemini API calls (lightweight, no DB needed)
# ──────────────────────────────────────────────

def call_gemini(prompt: str, system: str = "", model: str = None, json_mode: bool = False) -> str:
    """Call Gemini API synchronously."""
    from google import genai

    api_key = get_api_key()
    client = genai.Client(api_key=api_key)

    config_kwargs = {
        "temperature": 0.3,
    }
    if system:
        config_kwargs["system_instruction"] = system
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"

    config = genai.types.GenerateContentConfig(**config_kwargs)

    response = client.models.generate_content(
        model=model or CLARIFIER_MODEL,
        contents=prompt,
        config=config,
    )
    return response.text.strip()


# ──────────────────────────────────────────────
# Step 3: Intent analysis
# ──────────────────────────────────────────────

INTAKE_SYSTEM = """You are an intent analysis engine. Analyze the user's message and return JSON:
{
  "interpreted_intent": "clear sentence of what they want",
  "task_type": "code|writing|research|analysis|creative|data|math|system_design|debugging|conversation",
  "complexity": 1-10,
  "confidence_score": 0-100,
  "ambiguity_areas": ["list of unclear things"],
  "requires_brainstorming": true/false
}
Rules:
- Parse TRUE INTENT, not literal words
- Score confidence CONSERVATIVELY
- requires_brainstorming=true for any building/creative task
- Return ONLY valid JSON"""


def analyze_intent(message: str, user: dict) -> dict:
    """Analyze user intent with Gemini."""
    prompt = f"USER PROFILE: {json.dumps(user)}\n\nMESSAGE: {message}"

    with console.status("[#7c3aed]Analyzing your request...", spinner="dots"):
        raw = call_gemini(prompt, system=INTAKE_SYSTEM, json_mode=True)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "interpreted_intent": message[:200],
            "task_type": "code",
            "complexity": 5,
            "confidence_score": 60,
            "ambiguity_areas": ["Could not parse intent"],
            "requires_brainstorming": True,
        }

    # Display
    console.print()
    intent_table = Table(show_header=False, border_style="#4b5563", padding=(0, 1))
    intent_table.add_column("Key", style="#9ca3af", width=14)
    intent_table.add_column("Value", style="#e2e8f0")
    intent_table.add_row("Intent", data.get("interpreted_intent", ""))
    intent_table.add_row("Type", data.get("task_type", ""))
    intent_table.add_row("Complexity", f"{data.get('complexity', '?')}/10")
    intent_table.add_row("Confidence", f"{data.get('confidence_score', '?')}%")
    console.print(Panel(intent_table, title="[bold #7c3aed]Analysis[/]", border_style="#4b5563"))
    console.print()

    return data


# ──────────────────────────────────────────────
# Step 4: Clarifying questions
# ──────────────────────────────────────────────

CLARIFIER_SYSTEM = """You generate clarifying questions for an AI project builder. Return JSON:
{
  "questions": [
    {
      "question": "text",
      "question_type": "multiple_choice|yes_no|free_text",
      "options": ["A", "B", "C"],
      "default": "A",
      "why_it_matters": "brief reason"
    }
  ]
}
Rules:
- Max 4 questions
- PREFER multiple_choice with clear options
- ALWAYS provide a default
- For yes/no use question_type "yes_no"
- Don't ask what the profile already tells you
- Order by impact
- Return ONLY valid JSON"""


def ask_clarifications(message: str, intake: dict, user: dict) -> dict:
    """Generate and ask clarifying questions interactively."""
    prompt = (
        f"USER MESSAGE: {message}\n\n"
        f"INTENT ANALYSIS: {json.dumps(intake)}\n\n"
        f"USER PROFILE: {json.dumps(user)}"
    )

    with console.status("[#7c3aed]Generating questions...", spinner="dots"):
        raw = call_gemini(prompt, system=CLARIFIER_SYSTEM, json_mode=True)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    questions = data.get("questions", [])
    if not questions:
        return {}

    console.print(Rule("[bold #7c3aed]A few questions[/]", style="#4b5563"))
    console.print()

    answers = {}

    for i, q in enumerate(questions[:4], 1):
        q_text = q.get("question", "")
        q_type = q.get("question_type", "free_text")
        options = q.get("options", [])
        default = q.get("default", "")
        why = q.get("why_it_matters", "")

        if why:
            console.print(f"  [#6b7280]{why}[/]")

        if q_type == "yes_no":
            answer = questionary.confirm(
                q_text,
                default=default.lower() in ("yes", "true", "y"),
                style=PROMPT_STYLE,
            ).ask()
            answers[q_text] = "Yes" if answer else "No"

        elif q_type == "multiple_choice" and options:
            # Find default index
            choices = []
            for opt in options:
                choices.append(opt)

            answer = questionary.select(
                q_text,
                choices=choices,
                default=default if default in choices else None,
                style=PROMPT_STYLE,
            ).ask()
            answers[q_text] = answer if answer else default

        else:
            answer = questionary.text(
                q_text,
                default=default,
                style=PROMPT_STYLE,
            ).ask()
            answers[q_text] = answer if answer else default

        console.print()

    return answers


# ──────────────────────────────────────────────
# Step 5: Approach proposals
# ──────────────────────────────────────────────

APPROACH_SYSTEM = """You propose 2-3 different implementation approaches. Return JSON:
{
  "context_summary": "1-2 sentence summary incorporating user's answers",
  "approaches": [
    {
      "id": "a",
      "title": "Short name (3-6 words)",
      "description": "2-3 sentence description",
      "pros": ["pro1", "pro2"],
      "cons": ["con1"],
      "effort_level": "low|medium|high",
      "recommended": true/false
    }
  ]
}
Rules:
- Exactly 2-3 approaches
- They must be MEANINGFULLY different
- Mark exactly ONE as recommended
- Return ONLY valid JSON"""


def propose_approaches(message: str, intake: dict, qa: dict, user: dict) -> dict:
    """Generate approach proposals and let user pick."""
    prompt = (
        f"USER MESSAGE: {message}\n\n"
        f"INTENT: {json.dumps(intake)}\n\n"
        f"Q&A:\n" + "\n".join(f"Q: {q}\nA: {a}" for q, a in qa.items()) + "\n\n"
        f"USER PROFILE: {json.dumps(user)}"
    )

    with console.status("[#7c3aed]Brainstorming approaches...", spinner="dots"):
        raw = call_gemini(prompt, system=APPROACH_SYSTEM, json_mode=True)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    approaches = data.get("approaches", [])
    if not approaches:
        return None

    console.print(Rule("[bold #7c3aed]Pick an approach[/]", style="#4b5563"))
    console.print()

    if data.get("context_summary"):
        console.print(f"  [#9ca3af]{data['context_summary']}[/]")
        console.print()

    # Display approaches
    for approach in approaches:
        rec = " [#22d3ee](recommended)[/]" if approach.get("recommended") else ""
        effort_colors = {"low": "#22c55e", "medium": "#eab308", "high": "#ef4444"}
        effort = approach.get("effort_level", "medium")
        effort_styled = f"[{effort_colors.get(effort, '#9ca3af')}]{effort}[/]"

        console.print(Panel(
            f"[#e2e8f0]{approach.get('description', '')}[/]\n\n"
            f"[#22c55e]+ {('[/]\n[#22c55e]+ ').join(approach.get('pros', []))}[/]\n"
            f"[#ef4444]- {('[/]\n[#ef4444]- ').join(approach.get('cons', []))}[/]\n\n"
            f"Effort: {effort_styled}",
            title=f"[bold #7c3aed]{approach.get('id', '').upper()}[/] [bold #e2e8f0]{approach.get('title', '')}[/]{rec}",
            border_style="#4b5563",
            padding=(0, 2),
        ))

    # Let user pick
    choices = []
    default_choice = None
    approach_map = {}
    for a in approaches:
        label = f"{a['id'].upper()}: {a['title']}"
        choices.append(label)
        approach_map[label] = a
        if a.get("recommended"):
            default_choice = label

    selected_label = questionary.select(
        "Which approach?",
        choices=choices,
        default=default_choice,
        style=PROMPT_STYLE,
    ).ask()

    console.print()
    return approach_map.get(selected_label)


# ──────────────────────────────────────────────
# Step 6: Select skills (from backend or fallback)
# ──────────────────────────────────────────────

# Try to import backend skill engine
try:
    from backend.database import async_session_factory
    from backend.skills.skill_engine import select_skills as backend_select_skills
    HAS_BACKEND_SKILLS = True
except ImportError:
    HAS_BACKEND_SKILLS = False

# Inline skill definitions (fallback for standalone CLI use)
SKILL_TEMPLATES = {
    "chain_of_thought": "Think step by step, showing intermediate reasoning before the final answer.",
    "task_decomposition": "Break into numbered subtasks, complete each, then combine into final output.",
    "component_architecture": "Organize code into separate, clearly labeled files/components with a file tree first.",
    "expert_persona": "Approach as a senior expert with 15+ years experience. Apply best practices.",
    "error_handling_focus": "Implement robust error handling: validate inputs, handle failure modes, meaningful error messages.",
    "security_review": "Review for vulnerabilities: injection, XSS, auth bypass, secrets exposure.",
    "performance_awareness": "Consider time/space complexity, identify bottlenecks, suggest optimizations.",
    "concise_mode": "Be direct. Lead with the answer. No preamble. Every word earns its place.",
    "self_evaluation_rubric": "Score output on accuracy, completeness, clarity (1-5 each). Revise if below 4.",
    "markdown_formatting": "Use rich markdown: headers, bullets, tables, code blocks with language tags.",
    "test_generation": "Generate tests: happy path, edge cases, error cases. Arrange-Act-Assert pattern.",
}

SKILL_TASK_MAP = {
    "code": ["chain_of_thought", "task_decomposition", "component_architecture", "expert_persona", "error_handling_focus", "security_review"],
    "system_design": ["task_decomposition", "component_architecture", "expert_persona", "performance_awareness"],
    "creative": ["expert_persona", "markdown_formatting"],
    "writing": ["expert_persona", "markdown_formatting", "concise_mode"],
    "debugging": ["chain_of_thought", "error_handling_focus", "security_review"],
    "research": ["chain_of_thought", "markdown_formatting", "self_evaluation_rubric"],
    "analysis": ["chain_of_thought", "self_evaluation_rubric", "markdown_formatting"],
}


def _select_skills_fallback(task_type: str, complexity: int, user: dict) -> list[dict]:
    """Fallback skill selection when backend is unavailable."""
    skill_names = SKILL_TASK_MAP.get(task_type, ["expert_persona", "markdown_formatting"])

    # Add concise_mode for experts
    if user.get("technical_level") == "expert" and "concise_mode" not in skill_names:
        skill_names.append("concise_mode")

    # Add test_generation for complex code tasks
    if task_type == "code" and complexity >= 6 and "test_generation" not in skill_names:
        skill_names.append("test_generation")

    skills = []
    for name in skill_names[:5]:
        template = SKILL_TEMPLATES.get(name, "")
        if template:
            skills.append({"name": name, "implementation_template": template})

    return skills


def select_skills(task_type: str, complexity: int, user: dict) -> list[dict]:
    """Select relevant skills - uses backend if available, fallback otherwise."""
    if HAS_BACKEND_SKILLS:
        try:
            # Use asyncio to run the backend async function
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async def _get_skills():
                    async with async_session_factory() as session:
                        skills = await backend_select_skills(
                            task_type=task_type,
                            complexity=complexity,
                            user_profile=user,
                            session=session
                        )
                        return skills
                skills = loop.run_until_complete(_get_skills())
                if skills:
                    console.print("[blue]Using backend skill selection[/blue]")
                    return skills
            finally:
                loop.close()
        except Exception as e:
            console.print(f"[yellow]Backend skills unavailable ({e}), using fallback[/yellow]")
    
    return _select_skills_fallback(task_type, complexity, user)


# ──────────────────────────────────────────────
# Step 7: Select MCPs (from backend or fallback)
# ──────────────────────────────────────────────

# Try to import backend MCP selector
try:
    from backend.mcps.mcp_selector import select_mcps as backend_select_mcps
    HAS_BACKEND_MCPS = True
except ImportError:
    HAS_BACKEND_MCPS = False

AVAILABLE_MCPS = [
    {
        "name": "filesystem",
        "description": "Read, write, manage files in workspace",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "task_types": ["code", "system_design"],
        "keywords": ["file", "read", "write", "save", "create", "project"],
    },
    {
        "name": "memory",
        "description": "Persistent memory storage across sessions",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "task_types": [],
        "keywords": ["remember", "recall"],
    },
]


def _select_mcps_fallback(task_type: str, intent: str) -> list[dict]:
    """Fallback MCP selection when backend is unavailable."""
    active = []
    intent_lower = intent.lower()

    for mcp in AVAILABLE_MCPS:
        type_match = task_type in mcp["task_types"] if mcp["task_types"] else False
        keyword_match = any(kw in intent_lower for kw in mcp["keywords"])
        if type_match or keyword_match:
            active.append(mcp)

    return active


def select_mcps(task_type: str, intent: str) -> list[dict]:
    """Select relevant MCPs - uses backend if available, fallback otherwise."""
    if HAS_BACKEND_MCPS:
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async def _get_mcps():
                    async with async_session_factory() as session:
                        mcp_result = await backend_select_mcps(
                            task_type=task_type,
                            interpreted_intent=intent,
                            session=session
                        )
                        return mcp_result.get("active", [])
                mcps = loop.run_until_complete(_get_mcps())
                if mcps:
                    console.print("[blue]Using backend MCP selection[/blue]")
                    return mcps
            finally:
                loop.close()
        except Exception as e:
            console.print(f"[yellow]Backend MCPs unavailable ({e}), using fallback[/yellow]")
    
    return _select_mcps_fallback(task_type, intent)


# ──────────────────────────────────────────────
# Step 7.5: SkillKit Integration - Discover & Install Agent Skills
# ──────────────────────────────────────────────

def check_skillkit() -> bool:
    """Check if SkillKit is available."""
    try:
        result = subprocess.run(
            [BASH_EXECUTABLE, "-c", "npx skillkit@latest --version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def search_skills(query: str) -> list[dict]:
    """Search for skills using SkillKit."""
    try:
        result = subprocess.run(
            [BASH_EXECUTABLE, "-c", f'npx skillkit@latest find "{query}" --json'],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # Parse text output if JSON not available
                return _parse_skillkit_output(result.stdout)
        return []
    except Exception as e:
        console.print(f"[yellow]Skill search failed: {e}[/yellow]")
        return []


def _parse_skillkit_output(output: str) -> list[dict]:
    """Parse SkillKit text output into structured data."""
    skills = []
    lines = output.strip().split('\n')
    current_skill = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_skill:
                skills.append(current_skill)
                current_skill = {}
            continue
        
        # Try to extract skill info from output
        if ':' in line:
            key, value = line.split(':', 1)
            current_skill[key.strip().lower()] = value.strip()
    
    if current_skill:
        skills.append(current_skill)
    
    return skills


def install_skill(repo: str, skill_name: str = None) -> bool:
    """Install a skill using SkillKit."""
    try:
        cmd = f'npx skillkit@latest install {repo}'
        if skill_name:
            cmd += f' --skills {skill_name}'
        
        result = subprocess.run(
            [BASH_EXECUTABLE, "-c", cmd],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except Exception as e:
        console.print(f"[red]Skill installation failed: {e}[/red]")
        return False


def list_installed_skills() -> list[str]:
    """List installed skills."""
    try:
        result = subprocess.run(
            [BASH_EXECUTABLE, "-c", "npx skillkit@latest list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        return []
    except Exception:
        return []


def recommend_skills(task_type: str, intent: str) -> list[dict]:
    """Recommend skills based on task."""
    # Common skill mappings
    skill_queries = {
        "code": ["testing", "best practices"],
        "system_design": ["architecture", "patterns"],
        "creative": ["design", "creative"],
        "writing": ["documentation", "writing"],
        "debugging": ["debugging", "testing"],
        "research": ["research"],
    }
    
    queries = skill_queries.get(task_type, [])
    
    # Add specific technology keywords from intent
    intent_lower = intent.lower()
    tech_keywords = [
        "react", "vue", "angular", "next", "typescript", "python",
        "kubernetes", "docker", "aws", "security", "api", "database",
        "postgres", "prisma", "graphql", "rest"
    ]
    
    for keyword in tech_keywords:
        if keyword in intent_lower:
            queries.append(keyword)
    
    # Search for skills
    recommendations = []
    for query in queries[:3]:  # Limit to 3 searches
        results = search_skills(query)
        recommendations.extend(results[:2])  # Top 2 from each search
    
    return recommendations[:5]  # Return top 5 overall


def discover_and_install_skills(task_type: str, intent: str, user: dict) -> list[str]:
    """Interactive skill discovery and installation."""
    if not check_skillkit():
        console.print("[yellow]SkillKit not available. Install: npm i -g skillkit[/yellow]")
        return []
    
    console.print(Rule("[bold #7c3aed]Discover Agent Skills[/]", style="#4b5563"))
    console.print()
    console.print("[#9ca3af]Searching for relevant skills from the marketplace...[/]")
    console.print()
    
    # Get recommendations
    recommendations = recommend_skills(task_type, intent)
    
    if not recommendations:
        console.print("[#9ca3af]No specific skill recommendations found.[/]")
        console.print()
        return []
    
    # Show recommendations
    console.print("[bold #22d3ee]Found relevant skills:[/]")
    console.print()
    
    for i, skill in enumerate(recommendations, 1):
        name = skill.get('name', skill.get('title', 'Unknown'))
        desc = skill.get('description', skill.get('desc', 'No description'))
        repo = skill.get('repo', skill.get('source', 'unknown'))
        console.print(f"  [bold]{i}. {name}[/bold]")
        console.print(f"     [#9ca3af]{desc}[/]")
        console.print(f"     [#6b7280]Install: npx skillkit@latest install {repo}[/]")
        console.print()
    
    # Ask if user wants to install
    install_choice = questionary.confirm(
        "Install recommended skills?",
        default=False,
        style=PROMPT_STYLE,
    ).ask()
    
    installed = []
    if install_choice:
        with console.status("[#7c3aed]Installing skills...", spinner="dots"):
            for skill in recommendations:
                repo = skill.get('repo', skill.get('source'))
                skill_name = skill.get('name', skill.get('title'))
                if repo:
                    if install_skill(repo, skill_name):
                        installed.append(skill_name)
                        console.print(f"[#22c55e]✓ Installed: {skill_name}[/]")
                    else:
                        console.print(f"[#ef4444]✗ Failed: {skill_name}[/]")
    
    # Show all installed skills
    all_installed = list_installed_skills()
    if all_installed:
        console.print()
        console.print(f"[bold #22d3ee]Installed skills ({len(all_installed)}):[/]")
        for skill in all_installed[:10]:  # Show first 10
            console.print(f"  • {skill}")
        if len(all_installed) > 10:
            console.print(f"  [#9ca3af]... and {len(all_installed) - 10} more[/]")
    
    console.print()
    return all_installed


# ──────────────────────────────────────────────
# Step 7.6: Gemini-Kit Integration - AI Agents & Workflows
# ──────────────────────────────────────────────

GEMINI_KIT_AGENTS = {
    # Core Development
    "planner": {"name": "Planner", "emoji": "📋", "role": "Create detailed plans", "when": "Starting new features"},
    "scout": {"name": "Scout", "emoji": "🔍", "role": "Explore codebase", "when": "New projects, onboarding"},
    "coder": {"name": "Coder", "emoji": "💻", "role": "Write clean code", "when": "Implementing features"},
    "tester": {"name": "Tester", "emoji": "🧪", "role": "Write & run tests", "when": "Quality assurance"},
    "reviewer": {"name": "Reviewer", "emoji": "👀", "role": "Code review", "when": "Before merging PRs"},
    
    # Specialists
    "security-auditor": {"name": "Security Auditor", "emoji": "🔐", "role": "Security audit, OWASP", "when": "Security reviews"},
    "frontend-specialist": {"name": "Frontend Specialist", "emoji": "⚛️", "role": "React, Next.js, UI/UX", "when": "Frontend development"},
    "backend-specialist": {"name": "Backend Specialist", "emoji": "🖥️", "role": "API, Database, Docker", "when": "Backend development"},
    "devops-engineer": {"name": "DevOps Engineer", "emoji": "🚀", "role": "CI/CD, K8s, GitHub Actions", "when": "Infrastructure"},
    "debugger": {"name": "Debugger", "emoji": "🐛", "role": "Root cause analysis", "when": "Runtime errors"},
    "database-admin": {"name": "Database Admin", "emoji": "🗄️", "role": "Schema, migrations", "when": "Database work"},
    "fullstack": {"name": "Fullstack", "emoji": "🌐", "role": "End-to-end", "when": "Full features"},
    "performance-optimizer": {"name": "Performance Optimizer", "emoji": "⚡", "role": "Core Web Vitals", "when": "Performance issues"},
}

GEMINI_KIT_WORKFLOWS = [
    "explore", "plan-compound", "work", "review-compound", "compound",
    "housekeeping", "specs", "triage", "report-bug", "adr", "changelog"
]


def check_gemini_kit() -> dict:
    """Check if Gemini-Kit is installed and get info."""
    kit_path = Path.home() / ".gemini" / "extensions" / "gemini-kit"
    
    if not kit_path.exists():
        return {"installed": False, "path": None}
    
    # Check if built
    dist_path = kit_path / "dist"
    if not dist_path.exists():
        return {"installed": True, "built": False, "path": str(kit_path)}
    
    # Get available agents and workflows
    agents_path = kit_path / ".agent" / "agents"
    workflows_path = kit_path / ".agent" / "workflows"
    
    available_agents = []
    if agents_path.exists():
        available_agents = [f.stem for f in agents_path.glob("*.md")]
    
    available_workflows = []
    if workflows_path.exists():
        available_workflows = [f.stem for f in workflows_path.glob("*.md")]
    
    return {
        "installed": True,
        "built": True,
        "path": str(kit_path),
        "agents": available_agents,
        "workflows": available_workflows,
    }


def select_gemini_kit_agent(task_type: str, intent: str) -> dict:
    """Select appropriate Gemini-Kit agent based on task."""
    kit_info = check_gemini_kit()
    
    if not kit_info.get("installed") or not kit_info.get("built"):
        return None
    
    # Task type to agent mapping
    task_agent_map = {
        "code": ["coder", "frontend-specialist", "backend-specialist"],
        "system_design": ["planner", "backend-specialist", "devops-engineer"],
        "debugging": ["debugger", "security-auditor"],
        "creative": ["frontend-specialist", "coder"],
        "research": ["scout", "planner"],
        "analysis": ["scout", "reviewer"],
    }
    
    # Intent-based agent selection
    intent_lower = intent.lower()
    
    # Security
    if any(kw in intent_lower for kw in ["security", "audit", "vulnerability", "owasp"]):
        return GEMINI_KIT_AGENTS.get("security-auditor")
    
    # Frontend
    if any(kw in intent_lower for kw in ["react", "vue", "ui", "frontend", "component", "next.js"]):
        return GEMINI_KIT_AGENTS.get("frontend-specialist")
    
    # Backend
    if any(kw in intent_lower for kw in ["api", "backend", "database", "server", "postgres"]):
        return GEMINI_KIT_AGENTS.get("backend-specialist")
    
    # DevOps
    if any(kw in intent_lower for kw in ["docker", "kubernetes", "ci/cd", "deploy", "devops"]):
        return GEMINI_KIT_AGENTS.get("devops-engineer")
    
    # Performance
    if any(kw in intent_lower for kw in ["performance", "optimize", "speed", "slow"]):
        return GEMINI_KIT_AGENTS.get("performance-optimizer")
    
    # Fullstack
    if any(kw in intent_lower for kw in ["fullstack", "full stack", "end-to-end"]):
        return GEMINI_KIT_AGENTS.get("fullstack")
    
    # Default based on task type
    suggested_agents = task_agent_map.get(task_type, ["coder"])
    return GEMINI_KIT_AGENTS.get(suggested_agents[0]) if suggested_agents else None


def show_gemini_kit_agents() -> str:
    """Interactive agent selection."""
    kit_info = check_gemini_kit()
    
    if not kit_info.get("installed"):
        console.print("[yellow]Gemini-Kit not installed.[/yellow]")
        console.print("[#9ca3af]Install: git clone https://github.com/nth5693/gemini-kit.git ~/.gemini/extensions/gemini-kit[/]")
        return None
    
    if not kit_info.get("built"):
        console.print("[yellow]Gemini-Kit not built. Run: cd ~/.gemini/extensions/gemini-kit && npm install && npm run build[/yellow]")
        return None
    
    console.print(Rule("[bold #7c3aed]Gemini-Kit Agents[/]", style="#4b5563"))
    console.print()
    console.print("[bold #22d3ee]Available specialized AI agents:[/]")
    console.print()
    
    # Group agents
    core_agents = ["planner", "scout", "coder", "tester", "reviewer"]
    specialist_agents = ["security-auditor", "frontend-specialist", "backend-specialist", 
                         "devops-engineer", "debugger", "database-admin", "fullstack", 
                         "performance-optimizer"]
    
    # Show core agents
    console.print("[bold]Core Development:[/bold]")
    for agent_id in core_agents:
        if agent_id in GEMINI_KIT_AGENTS:
            agent = GEMINI_KIT_AGENTS[agent_id]
            console.print(f"  {agent['emoji']} [bold]{agent['name']}[/bold] - {agent['role']}")
    console.print()
    
    # Show specialists
    console.print("[bold]Specialists:[/bold]")
    for agent_id in specialist_agents:
        if agent_id in GEMINI_KIT_AGENTS:
            agent = GEMINI_KIT_AGENTS[agent_id]
            console.print(f"  {agent['emoji']} [bold]{agent['name']}[/bold] - {agent['role']}")
    console.print()
    
    # Ask to select
    choices = []
    for agent_id, agent in GEMINI_KIT_AGENTS.items():
        label = f"{agent['emoji']} {agent['name']} - {agent['role']}"
        choices.append(questionary.Choice(label, value=agent_id))
    
    choices.insert(0, questionary.Choice("⚙️ Auto-select based on task", value="auto"))
    choices.append(questionary.Choice("❌ Don't use Gemini-Kit agent", value="none"))
    
    selected = questionary.select(
        "Which agent would you like to use?",
        choices=choices,
        style=PROMPT_STYLE,
    ).ask()
    
    console.print()
    return selected


# ──────────────────────────────────────────────
# Step 8: Build the optimized prompt
# ──────────────────────────────────────────────

OPTIMIZER_SYSTEM = """You are a prompt engineering optimizer. Transform raw context into a PERFECT, self-contained prompt for an AI coding agent.

Your output must be a COMPLETE prompt ready to send. Include:
1. Role & expertise assignment
2. User context (level, preferences)
3. Full task description — inline everything
4. Skills woven in NATURALLY (not as bullet lists)
5. Tool instructions if tools are available
6. Constraints/boundaries
7. Output format instructions
8. Quality checklist

CRITICAL for code tasks: instruct the model to format files as:
File: path/to/file.ext
```language
<code>
```

Include ALL files needed for a working project. The output must be runnable.

Output ONLY the prompt. No meta-commentary. No "Here's your prompt:". Just the prompt itself."""


def build_prompt(
    message: str,
    intake: dict,
    qa: dict,
    approach: dict,
    user: dict,
    skills: list,
    mcps: list,
    agent_skills: list = None,
    gemini_kit_agent: dict = None,
) -> str:
    """Build the optimized prompt using Gemini."""
    sections = []

    # Add Gemini-Kit agent role if selected
    if gemini_kit_agent:
        sections.append(
            f"=== YOUR ROLE (Gemini-Kit Agent) ===\n"
            f"You are the {gemini_kit_agent['emoji']} {gemini_kit_agent['name']} agent.\n"
            f"Role: {gemini_kit_agent['role']}\n"
            f"Best used when: {gemini_kit_agent['when']}\n\n"
            f"As this specialized agent, bring your expert knowledge and focus to this task."
        )

    sections.append(f"=== USER MESSAGE ===\n{message}")
    sections.append(f"=== INTENT ===\n{json.dumps(intake, indent=2)}")

    if qa:
        qa_text = "\n".join(f"Q: {q}\nA: {a}" for q, a in qa.items())
        sections.append(f"=== CLARIFICATION Q&A ===\n{qa_text}")

    sections.append(f"=== USER PROFILE ===\n{json.dumps(user, indent=2)}")

    if skills:
        skill_text = "\n".join(f"- {s['name']}: {s['implementation_template']}" for s in skills)
        sections.append(f"=== SKILLS (weave naturally) ===\n{skill_text}")

    if agent_skills:
        agent_skill_text = "\n".join(f"- {s}" for s in agent_skills[:10])
        sections.append(f"=== INSTALLED AGENT SKILLS (you have access to these) ===\n{agent_skill_text}\nNote: These are community-vetted skills. Use them when relevant to the task.")

    if mcps:
        mcp_text = "\n".join(f"- {m['name']}: {m['description']}" for m in mcps)
        sections.append(f"=== AVAILABLE TOOLS ===\n{mcp_text}")

    if approach:
        sections.append(
            f"=== CHOSEN APPROACH ===\n"
            f"Title: {approach.get('title', '')}\n"
            f"Description: {approach.get('description', '')}\n"
            f"Pros: {', '.join(approach.get('pros', []))}\n"
            f"Cons: {', '.join(approach.get('cons', []))}"
        )

    meta_prompt = "\n\n".join(sections)

    with console.status("[#7c3aed]Crafting the perfect prompt...", spinner="dots"):
        optimized = call_gemini(meta_prompt, system=OPTIMIZER_SYSTEM, model=CLARIFIER_MODEL)

    if not optimized or len(optimized) < 50:
        # Fallback: manual assembly
        optimized = _fallback_prompt(message, intake, qa, approach, user, skills, agent_skills, gemini_kit_agent)

    return optimized


def _fallback_prompt(message, intake, qa, approach, user, skills, agent_skills=None, gemini_kit_agent=None):
    """Manual prompt assembly when optimizer fails."""
    parts = []
    
    # Add Gemini-Kit agent role first
    if gemini_kit_agent:
        parts.append(f"You are the {gemini_kit_agent['emoji']} {gemini_kit_agent['name']} agent from Gemini-Kit.")
        parts.append(f"Your specialty: {gemini_kit_agent['role']}")
        parts.append(f"You excel at: {gemini_kit_agent['when']}")
        parts.append("")
    
    task_type = intake.get("task_type", "code")
    roles = {
        "code": "senior software engineer",
        "system_design": "senior systems architect",
        "creative": "creative director",
        "writing": "professional writer",
    }
    
    if not gemini_kit_agent:
        parts.append(f"You are a {roles.get(task_type, 'expert assistant')} with 15+ years of experience.")

    if user.get("technical_level") == "expert":
        parts.append("The user is an expert. Be concise, use precise technical language.")
    elif user.get("technical_level") == "non_technical":
        parts.append("The user is non-technical. Use plain language, explain concepts.")

    if user.get("stack"):
        parts.append(f"Tech stack: {', '.join(user['stack'])}")

    parts.append(f"\nTASK: {intake.get('interpreted_intent', message)}")

    if qa:
        parts.append("\nCLARIFICATION:")
        for q, a in qa.items():
            parts.append(f"Q: {q}\nA: {a}")

    if approach:
        parts.append(f"\nAPPROACH: {approach.get('title', '')}\n{approach.get('description', '')}")

    if skills:
        parts.append("\nGUIDELINES:")
        for s in skills:
            parts.append(f"- {s['implementation_template']}")
    
    if agent_skills:
        parts.append("\nINSTALLED AGENT SKILLS:")
        parts.append("You have access to these community-vetted skills:")
        for s in agent_skills[:10]:
            parts.append(f"- {s}")

    parts.append(f"\nUSER REQUEST:\n{message}")
    return "\n\n".join(parts)


# ──────────────────────────────────────────────
# Step 9: Execute via Gemini CLI or API
# ──────────────────────────────────────────────

def check_gemini_cli() -> bool:
    """Check if Gemini CLI is installed."""
    return shutil.which("gemini") is not None


def initialize_project_dir(project_dir: Path, skills: list, agent_skills: list, mcps: list, gemini_kit_agent: dict = None) -> None:
    """Initialize project directory with industry-standard AI instruction files."""
    # Create directory structure
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gemini directory (standard for Gemini CLI)
    gemini_dir = project_dir / ".gemini"
    gemini_dir.mkdir(exist_ok=True)
    
    # Build instructions content that Gemini CLI reads automatically
    instructions_parts = []
    
    # Add agent role if using Gemini-Kit
    if gemini_kit_agent:
        instructions_parts.append(f"""# Agent Role

You are the {gemini_kit_agent.get('emoji')} {gemini_kit_agent.get('name')} agent.
Role: {gemini_kit_agent.get('role')}
Best used when: {gemini_kit_agent.get('when')}

As this specialized agent, bring your expert knowledge and focus to this task.
""")
    
    # Add skills
    if skills:
        instructions_parts.append("# Applied Skills\n")
        for s in skills:
            instructions_parts.append(f"## {s.get('name')}\n{s.get('implementation_template')}\n")
    
    # Add agent skills
    if agent_skills:
        instructions_parts.append("# Installed Agent Skills\n")
        instructions_parts.append("You have access to these community-vetted skills:\n")
        for skill in agent_skills[:20]:
            instructions_parts.append(f"- {skill}")
        instructions_parts.append("")
    
    # Add MCP tools
    if mcps:
        instructions_parts.append("# Available Tools (MCP)\n")
        for mcp in mcps:
            instructions_parts.append(f"## {mcp.get('name')}\n{mcp.get('description')}\n")
    
    instructions_content = "\n".join(instructions_parts)
    
    # Write .gemini/instructions.md (read by Gemini CLI automatically)
    (gemini_dir / "instructions.md").write_text(instructions_content, encoding="utf-8")
    
    # Write .gemini/config.json to configure shell execution
    gemini_config = {
        "shell": get_bash_executable() if sys.platform == "win32" else "/bin/bash",
        "shellArgs": ["-c"],
        "env": {
            "SHELL": get_bash_executable() if sys.platform == "win32" else "/bin/bash",
            "NODE_NO_READLINE": "1",
            "TERM": "dumb"
        }
    }
    (gemini_dir / "config.json").write_text(json.dumps(gemini_config, indent=2), encoding="utf-8")
    
    # Write .cursorrules (industry standard for AI tools like Cursor)
    cursorrules_content = instructions_content.replace("# ", "## ").replace("## Agent Role", "# Agent Role")
    (project_dir / ".cursorrules").write_text(cursorrules_content, encoding="utf-8")
    
    # Write INSTRUCTIONS.md at root (common standard)
    (project_dir / "INSTRUCTIONS.md").write_text(instructions_content, encoding="utf-8")
    
    bash_path = get_bash_executable() if sys.platform == "win32" else "/bin/bash"
    console.print(f"[#6b7280]✓ Initialized project: {project_dir}[/]")
    console.print(f"[#6b7280]✓ Created .gemini/instructions.md (Gemini CLI)[/]")
    console.print(f"[#6b7280]✓ Created .gemini/config.json (shell: {bash_path})[/]")
    console.print(f"[#6b7280]✓ Created .cursorrules (Cursor/AI tools)[/]")
    console.print(f"[#6b7280]✓ Created INSTRUCTIONS.md (root)[/]")
    console.print()


def execute_with_gemini_cli(prompt: str, project_dir: Path) -> dict:
    """Execute prompt using Gemini CLI with --yolo flag."""
    project_dir.mkdir(parents=True, exist_ok=True)

    output_log = project_dir / "brainstorm-output.log"
    prompt_file = project_dir / "GEMINI.md"

    # Write prompt to a file (safer than passing via command line)
    prompt_file.write_text(prompt, encoding="utf-8")
    
    # Verify the file was written correctly
    if not prompt_file.exists() or prompt_file.stat().st_size == 0:
        return {"success": False, "error": "Failed to write prompt file"}

    console.print()
    console.print(Panel(
        f"[#e2e8f0]Project directory:[/] [#22d3ee]{project_dir}[/]\n"
        f"[#e2e8f0]Prompt saved to:[/] [#22d3ee]{prompt_file.name}[/]\n"
        f"[#e2e8f0]Prompt size:[/] [#22d3ee]{len(prompt)} chars ({prompt_file.stat().st_size} bytes)[/]\n"
        f"[#e2e8f0]Output log:[/] [#22d3ee]{output_log.name}[/]",
        title="[bold #7c3aed]Gemini CLI[/]",
        border_style="#4b5563",
    ))
    
    # Show prompt preview
    console.print()
    console.print("[#9ca3af]Prompt preview (first 200 chars):[/]")
    preview = prompt[:200].replace("\n", " ")
    console.print(f"[#6b7280]{preview}...[/]")
    console.print()

    # Build the gemini command - use bash consistently to avoid nested shell issues
    # This way Gemini CLI's tool execution uses the same shell (bash)
    if sys.platform == "win32":
        # Use bash on Windows for consistency with tool execution
        cmd = f'cd "{project_dir}" && cat GEMINI.md | gemini --yolo > brainstorm-output.log 2>&1'
        shell_cmd = [BASH_EXECUTABLE, "-c", cmd]
        shell_name = "bash (Git Bash)"
    else:
        # Use bash on Unix
        cmd = f'cat "{prompt_file.name}" | gemini --yolo > "{output_log.name}" 2>&1'
        shell_cmd = [BASH_EXECUTABLE, "-c", cmd]
        shell_name = "bash"

    console.print()
    console.print(f"[#9ca3af]Starting Gemini CLI in {shell_name}...[/]")
    console.print(f"[#6b7280]Command: cat GEMINI.md | gemini --yolo[/]")
    console.print(f"[#6b7280]Working dir: {project_dir}[/]")
    console.print(f"[#6b7280]Shell for tools: bash (configured in .gemini/config.json)[/]")
    console.print()

    try:
        # Configure environment for proper shell execution in Gemini CLI
        env = os.environ.copy()
        env.update({
            "SHELL": BASH_EXECUTABLE,  # Tell Gemini CLI to use bash for tool execution
            "NODE_NO_READLINE": "1",   # Disable Node.js readline
            "TERM": "dumb",            # Non-interactive terminal
            "FORCE_COLOR": "0",        # Disable color codes that might break parsing
            "NO_COLOR": "1",           # Another standard for disabling colors
        })
        
        # Use native shell to avoid node-pty console attachment issues on Windows
        process = subprocess.Popen(
            shell_cmd,
            cwd=str(project_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Monitor output with timeout protection
        console.print("[#9ca3af]Gemini CLI is running. Monitoring output...[/]")
        console.print("[#6b7280]Press Ctrl+C to stop monitoring (process continues in background)[/]")
        console.print()

        last_size = 0
        no_output_count = 0
        max_no_output_iterations = 150  # 5 minutes (150 * 2 seconds)
        
        try:
            while process.poll() is None:
                time.sleep(2)
                
                # Check for output
                if output_log.exists():
                    current_size = output_log.stat().st_size
                    if current_size > last_size:
                        with open(output_log, "r", encoding="utf-8", errors="replace") as f:
                            f.seek(last_size)
                            new_content = f.read()
                            if new_content.strip():
                                console.print(new_content, end="")
                                no_output_count = 0  # Reset counter on new output
                        last_size = current_size
                    else:
                        no_output_count += 1
                else:
                    no_output_count += 1
                
                # Timeout protection: if no output for too long, warn but continue
                if no_output_count >= max_no_output_iterations:
                    console.print()
                    console.print("[#eab308]⚠ Warning: No output for 5 minutes. Process may be stuck.[/]")
                    console.print("[#9ca3af]Process is still running in background. Check logs later.[/]")
                    break

        except KeyboardInterrupt:
            console.print()
            console.print("[#eab308]Stopped monitoring. Gemini CLI continues in background.[/]")
            console.print(f"[#9ca3af]Check output: {output_log}[/]")

        # Final read of output
        if output_log.exists():
            with open(output_log, "r", encoding="utf-8", errors="replace") as f:
                f.seek(last_size)
                remaining = f.read()
                if remaining.strip():
                    console.print(remaining, end="")
        
        console.print()
        console.print()
        
        # Check process exit code
        exit_code = process.poll()
        if exit_code is not None and exit_code != 0:
            console.print(f"[#eab308]⚠ Gemini CLI exited with code {exit_code}[/]")
            
            # Check if any files were created (partial success)
            created_files = []
            if project_dir.exists():
                for item in project_dir.rglob("*"):
                    if item.is_file() and item.name not in ["GEMINI.md", "brainstorm-output.log", "INSTRUCTIONS.md", ".cursorrules"]:
                        if not item.name.endswith(".json") or ".gemini" not in str(item):
                            created_files.append(item)
            
            if created_files:
                console.print(f"[#22d3ee]✓ Partial success: {len(created_files)} files created before exit[/]")
                for f in created_files[:5]:
                    console.print(f"  [#6b7280]- {f.relative_to(project_dir)}[/]")
                if len(created_files) > 5:
                    console.print(f"  [#6b7280]... and {len(created_files) - 5} more[/]")
            else:
                console.print("[#ef4444]No files were created. Check the logs for errors.[/]")
            
            # Read stderr if available
            try:
                stderr_output = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
                if stderr_output.strip():
                    console.print()
                    console.print("[#ef4444]Error output:[/]")
                    console.print(f"[#9ca3af]{stderr_output[:500]}[/]")
            except Exception:
                pass
        
        # Verify we got output
        if output_log.exists() and output_log.stat().st_size > 0:
            if exit_code == 0 or exit_code is None:
                console.print("[#22c55e]✓ Gemini CLI completed successfully[/]")
            console.print(f"[#9ca3af]Output size: {output_log.stat().st_size} bytes[/]")
        else:
            console.print("[#ef4444]⚠ Warning: No output generated.[/]")
            console.print(f"[#9ca3af]Check prompt file: {prompt_file}[/]")
            console.print(f"[#9ca3af]Check output log: {output_log}[/]")
            
            # Offer retry option
            console.print()
            console.print("[#eab308]Possible issues:[/]")
            console.print("  [#6b7280]1. Gemini API key not configured[/]")
            console.print("  [#6b7280]2. Network connectivity issues[/]")
            console.print("  [#6b7280]3. Prompt file not readable[/]")
            console.print("  [#6b7280]4. Gemini CLI version incompatibility[/]")

        # Always return success if we got here (even with warnings)
        # The presence of output_log and project_dir means work was done
        return {
            "success": True,
            "output_log": str(output_log),
            "project_dir": str(project_dir),
            "exit_code": exit_code,
            "partial": exit_code != 0 if exit_code is not None else False,
        }

    except FileNotFoundError as e:
        console.print()
        console.print(f"[#ef4444]Error: {e}[/]")
        console.print("[#9ca3af]Gemini CLI not found. Install: npm install -g @google/generative-ai-cli[/]")
        return {"success": False, "error": "gemini CLI not found. Install it first."}
    
    except PermissionError as e:
        console.print()
        console.print(f"[#ef4444]Permission Error: {e}[/]")
        console.print("[#9ca3af]Cannot write to project directory or execute shell commands.[/]")
        return {"success": False, "error": f"Permission denied: {e}"}
    
    except subprocess.TimeoutExpired:
        console.print()
        console.print("[#ef4444]Process timed out after extended period.[/]")
        console.print("[#9ca3af]Try reducing complexity or breaking into smaller tasks.[/]")
        try:
            process.kill()
        except Exception:
            pass
        return {"success": False, "error": "Process timed out"}
    
    except Exception as e:
        console.print()
        console.print(f"[#ef4444]Unexpected error: {e}[/]")
        console.print(f"[#9ca3af]Error type: {type(e).__name__}[/]")
        
        # Try to save error state
        error_log = project_dir / "error.log"
        try:
            error_log.write_text(f"Error: {e}\nType: {type(e).__name__}\n", encoding="utf-8")
            console.print(f"[#9ca3af]Error details saved to: {error_log}[/]")
        except Exception:
            pass
        
        return {"success": False, "error": str(e)}


def execute_with_api(prompt: str, project_dir: Path) -> dict:
    """Execute prompt using Gemini API directly (fallback when CLI not available)."""
    from google import genai

    api_key = get_api_key()
    client = genai.Client(api_key=api_key)

    project_dir.mkdir(parents=True, exist_ok=True)

    console.print()
    console.print(Panel(
        f"[#e2e8f0]Using Gemini API (CLI not found)[/]\n"
        f"[#e2e8f0]Model:[/] [#22d3ee]{GEMINI_MODEL}[/]\n"
        f"[#e2e8f0]Project dir:[/] [#22d3ee]{project_dir}[/]",
        title="[bold #7c3aed]Executing[/]",
        border_style="#4b5563",
    ))
    console.print()

    with console.status("[#7c3aed]Generating with Gemini...", spinner="dots"):
        config = genai.types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=65536,
        )
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
        content = response.text or ""

    # Save prompt and response
    (project_dir / "GEMINI.md").write_text(prompt, encoding="utf-8")
    (project_dir / "brainstorm-output.md").write_text(content, encoding="utf-8")

    # Extract and write files
    files_written = extract_and_write_files(content, project_dir)

    return {
        "success": True,
        "content": content,
        "files_written": files_written,
        "project_dir": str(project_dir),
    }


def extract_and_write_files(content: str, project_dir: Path) -> list[str]:
    """Extract file blocks from AI response and write them to disk."""
    files = []
    seen = set()

    # Pattern: File: path/to/file.ext followed by ```
    pattern = re.compile(
        r'(?:^|\n)(?:#+ )?(?:File|file|Filename|filename)[:\s]+([^\n]+\.\w+)\s*\n'
        r'```[\w]*\n(.*?)```',
        re.DOTALL
    )
    for match in pattern.finditer(content):
        filepath = match.group(1).strip().strip('`"\'')
        code = match.group(2)
        if filepath and code and filepath not in seen and not filepath.startswith("http"):
            normalized = os.path.normpath(filepath)
            if normalized.startswith("..") or os.path.isabs(normalized):
                continue
            target = project_dir / normalized
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(code, encoding="utf-8")
            files.append(filepath)
            seen.add(filepath)

    # Pattern 2: ```language:filepath
    pattern2 = re.compile(
        r'```\w*[:\s]+([^\n`]+\.\w+)\s*\n(.*?)```',
        re.DOTALL
    )
    for match in pattern2.finditer(content):
        filepath = match.group(1).strip().strip('`"\'')
        code = match.group(2)
        if filepath and code and filepath not in seen and not filepath.startswith("http"):
            normalized = os.path.normpath(filepath)
            if normalized.startswith("..") or os.path.isabs(normalized):
                continue
            target = project_dir / normalized
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(code, encoding="utf-8")
            files.append(filepath)
            seen.add(filepath)

    return files


# ──────────────────────────────────────────────
# Step 10: Post-execution (install deps, start dev server)
# ──────────────────────────────────────────────

def detect_project_type(project_dir: Path) -> str:
    """Detect project type from files in directory."""
    if (project_dir / "package.json").exists():
        try:
            pkg = json.loads((project_dir / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                return "nextjs"
            if "vite" in deps:
                return "vite"
        except Exception:
            pass
        return "node"
    if (project_dir / "requirements.txt").exists():
        return "python"
    if any(project_dir.glob("*.html")):
        return "static"
    return "unknown"


def post_execution(project_dir: Path, files_written: list[str]):
    """Install dependencies and optionally start dev server."""
    if not files_written:
        console.print("[#9ca3af]No files were created. Nothing to run.[/]")
        return

    console.print()
    console.print(Rule("[bold #7c3aed]Project created[/]", style="#4b5563"))
    console.print()

    # Show files
    file_table = Table(show_header=False, border_style="#4b5563", padding=(0, 1))
    file_table.add_column("File", style="#22d3ee")
    for f in files_written[:20]:
        file_table.add_row(f)
    if len(files_written) > 20:
        file_table.add_row(f"... and {len(files_written) - 20} more")
    console.print(Panel(file_table, title=f"[bold #7c3aed]{len(files_written)} files[/]", border_style="#4b5563"))

    project_type = detect_project_type(project_dir)

    if project_type == "unknown":
        console.print(f"\n[#9ca3af]Project at: {project_dir}[/]")
        return

    # Ask about installing deps
    install = questionary.confirm(
        f"Install dependencies? (detected: {project_type})",
        default=True,
        style=PROMPT_STYLE,
    ).ask()

    if install:
        console.print()
        with console.status(f"[#7c3aed]Installing dependencies...", spinner="dots"):
            if project_type in ("nextjs", "vite", "node"):
                for pm in ["pnpm", "npm"]:
                    if shutil.which(pm):
                        result = subprocess.run(
                            [BASH_EXECUTABLE, "-c", f"{pm} install"],
                            cwd=str(project_dir),
                            capture_output=True,
                            text=True,
                            timeout=180,
                        )
                        if result.returncode == 0:
                            console.print(f"[#22c55e]Dependencies installed with {pm}[/]")
                        else:
                            console.print(f"[#ef4444]Install failed: {result.stderr[:200]}[/]")
                        break
            elif project_type == "python":
                result = subprocess.run(
                    [BASH_EXECUTABLE, "-c", f"{sys.executable} -m pip install -r requirements.txt"],
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                if result.returncode == 0:
                    console.print("[#22c55e]Dependencies installed[/]")
                else:
                    console.print(f"[#ef4444]Install failed: {result.stderr[:200]}[/]")

    # Ask about dev server
    if project_type in ("nextjs", "vite", "node", "python", "static"):
        start_server = questionary.confirm(
            "Start dev server?",
            default=True,
            style=PROMPT_STYLE,
        ).ask()

        if start_server:
            start_dev(project_dir, project_type)


def start_dev(project_dir: Path, project_type: str):
    """Start the dev server."""
    cmd = None
    port = None

    if project_type in ("nextjs", "vite", "node"):
        for pm in ["pnpm", "npm"]:
            if shutil.which(pm):
                cmd = [pm, "run", "dev"]
                port = 3000 if project_type == "nextjs" else 5173
                break
    elif project_type == "python":
        if (project_dir / "manage.py").exists():
            cmd = [sys.executable, "manage.py", "runserver"]
            port = 8000
        elif (project_dir / "app.py").exists():
            cmd = [sys.executable, "app.py"]
            port = 8000
        elif (project_dir / "main.py").exists():
            cmd = [sys.executable, "main.py"]
            port = 8000
    elif project_type == "static":
        cmd = [sys.executable, "-m", "http.server", "8080"]
        port = 8080

    if not cmd:
        console.print("[#9ca3af]Could not determine how to start this project.[/]")
        return

    console.print()
    console.print(f"[#22d3ee]Starting dev server on port {port} in bash...[/]")
    console.print(f"[#9ca3af]Press Ctrl+C to stop[/]")
    console.print()

    try:
        # Convert list command to string for bash execution
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
        process = subprocess.Popen(
            [BASH_EXECUTABLE, "-c", cmd_str],
            cwd=str(project_dir),
        )
        console.print(f"[bold #22c55e]Dev server running at http://localhost:{port}[/]")
        console.print()
        process.wait()
    except KeyboardInterrupt:
        console.print()
        console.print("[#eab308]Dev server stopped.[/]")
    except Exception as e:
        console.print(f"[#ef4444]Failed to start dev server: {e}[/]")


# ──────────────────────────────────────────────
# Main flow
# ──────────────────────────────────────────────

def get_project_dir_from_intent(intent: str) -> Path:
    """Generate a project directory path from the intent."""
    slug = re.sub(r'[^\w\- ]', '', intent.lower().strip())
    slug = re.sub(r'\s+', '-', slug)[:50].strip('-')
    if not slug:
        slug = "brainstorm-project"
    return Path.home() / "dev" / slug


def main():
    """Main CLI entry point."""
    header()

    # Verify API key
    get_api_key()

    # Step 1: Who are you?
    user = ask_who_you_are()

    # Step 2: What to build?
    message = ask_what_to_build()

    # Step 3: Analyze intent
    intake = analyze_intent(message, user)

    # Step 4: Clarifying questions
    qa = {}
    if intake.get("requires_brainstorming") or intake.get("confidence_score", 100) < 85:
        qa = ask_clarifications(message, intake, user)

    # Step 5: Approach proposals (for brainstorming tasks)
    approach = None
    if intake.get("requires_brainstorming") and qa:
        approach = propose_approaches(message, intake, qa, user)

    # Step 6: Select skills
    skills = select_skills(
        intake.get("task_type", "code"),
        intake.get("complexity", 5),
        user,
    )

    # Step 7: Select MCPs
    mcps = select_mcps(
        intake.get("task_type", "code"),
        intake.get("interpreted_intent", message),
    )

    # Step 7.5: Discover and install agent skills from marketplace
    agent_skills = []
    if questionary.confirm(
        "Search for relevant agent skills from marketplace?",
        default=True,
        style=PROMPT_STYLE,
    ).ask():
        agent_skills = discover_and_install_skills(
            intake.get("task_type", "code"),
            intake.get("interpreted_intent", message),
            user,
        )

    # Step 7.6: Select Gemini-Kit agent (auto-enable when available)
    gemini_kit_agent = None
    kit_info = check_gemini_kit()
    
    if kit_info.get("installed") and kit_info.get("built"):
        console.print(f"[bold #22d3ee]✓ Gemini-Kit detected ({len(kit_info.get('agents', []))} agents) - Auto-enabling[/]")
        console.print()
        
        # Auto-select agent based on task type
        gemini_kit_agent = select_gemini_kit_agent(
            intake.get("task_type", "code"),
            intake.get("interpreted_intent", message),
        )
        
        if gemini_kit_agent:
            console.print(f"[bold #22c55e]→ Auto-selected: {gemini_kit_agent['emoji']} {gemini_kit_agent['name']}[/]")
            console.print()

    # Display selections
    console.print(Rule("[bold #7c3aed]Building prompt[/]", style="#4b5563"))
    console.print()

    info_table = Table(show_header=False, border_style="#4b5563", padding=(0, 1))
    info_table.add_column("", style="#9ca3af", width=12)
    info_table.add_column("", style="#e2e8f0")
    info_table.add_row("Skills", ", ".join(s["name"] for s in skills) if skills else "none")
    info_table.add_row("Tools", ", ".join(m["name"] for m in mcps) if mcps else "none")
    if agent_skills:
        info_table.add_row("Agent Skills", f"{len(agent_skills)} installed")
    if gemini_kit_agent:
        info_table.add_row("Kit Agent", f"{gemini_kit_agent['emoji']} {gemini_kit_agent['name']}")
    if approach:
        info_table.add_row("Approach", approach.get("title", ""))
    console.print(info_table)
    console.print()

    # Step 8: Build optimized prompt with agent skills and Gemini-Kit agent
    prompt = build_prompt(message, intake, qa, approach, user, skills, mcps, agent_skills, gemini_kit_agent)
    
    # Show prompt composition summary
    console.print()
    console.print("[#9ca3af]Prompt composition:[/]")
    components = []
    if gemini_kit_agent:
        components.append(f"✓ Gemini-Kit Agent ({gemini_kit_agent['name']})")
    components.append(f"✓ User intent & context")
    if qa:
        components.append(f"✓ Clarifications ({len(qa)} Q&A)")
    if approach:
        components.append(f"✓ Approach strategy")
    if skills:
        components.append(f"✓ Skills ({len(skills)} applied)")
    if agent_skills:
        components.append(f"✓ Agent Skills ({len(agent_skills)} installed)")
    if mcps:
        components.append(f"✓ MCP Tools ({len(mcps)} available)")
    
    for comp in components:
        console.print(f"  [#6b7280]{comp}[/]")
    console.print(f"  [bold #22d3ee]Total: {len(prompt)} characters[/]")
    console.print()

    # Step 9: Choose execution method
    project_dir = get_project_dir_from_intent(intake.get("interpreted_intent", message))

    has_cli = check_gemini_cli()

    if has_cli:
        exec_method = questionary.select(
            "How to execute?",
            choices=[
                questionary.Choice("Gemini CLI (--yolo, runs in project dir)", value="cli"),
                questionary.Choice("Gemini API (generate + scaffold files)", value="api"),
                questionary.Choice("Just show me the prompt (copy/paste)", value="prompt"),
            ],
            style=PROMPT_STYLE,
        ).ask()
    else:
        exec_method = questionary.select(
            "How to execute?",
            choices=[
                questionary.Choice("Gemini API (generate + scaffold files)", value="api"),
                questionary.Choice("Just show me the prompt (copy/paste)", value="prompt"),
            ],
            style=PROMPT_STYLE,
        ).ask()

    if not exec_method:
        exec_method = "prompt"
    
    # Option to preview prompt before execution (for CLI method)
    if exec_method == "cli":
        if questionary.confirm(
            "Preview the full prompt before sending to Gemini?",
            default=False,
            style=PROMPT_STYLE,
        ).ask():
            console.print()
            console.print(Rule("[bold #7c3aed]Prompt Preview[/]", style="#4b5563"))
            console.print()
            # Show first 1000 chars
            preview_len = min(1000, len(prompt))
            console.print(Panel(
                f"[#e2e8f0]{prompt[:preview_len]}[/]\n\n[#9ca3af]... (total {len(prompt)} chars)[/]",
                border_style="#4b5563",
                padding=(1, 2),
            ))
            console.print()
            
            if not questionary.confirm("Continue with execution?", default=True, style=PROMPT_STYLE).ask():
                console.print("[#eab308]Execution cancelled.[/]")
                return

    if exec_method == "prompt":
        # Initialize project directory with skills
        initialize_project_dir(project_dir, skills, agent_skills, mcps, gemini_kit_agent)
        
        console.print()
        console.print(Rule("[bold #7c3aed]Your prompt[/]", style="#4b5563"))
        console.print()
        console.print(Panel(
            Markdown(prompt),
            border_style="#4b5563",
            padding=(1, 2),
        ))

        # Also save to file
        prompt_file = project_dir / "GEMINI.md"
        prompt_file.write_text(prompt, encoding="utf-8")
        console.print(f"\n[#9ca3af]Prompt saved to: {prompt_file}[/]")

    elif exec_method == "cli":
        # Initialize project directory with skills
        initialize_project_dir(project_dir, skills, agent_skills, mcps, gemini_kit_agent)
        
        result = execute_with_gemini_cli(prompt, project_dir)
        if result.get("success"):
            console.print()
            
            # Check if it was a partial success (early exit)
            if result.get("partial"):
                console.print("[#eab308]⚠ Partial completion detected.[/]")
                console.print(f"[#9ca3af]Exit code: {result.get('exit_code')}[/]")
                
                # Check if any files were created
                created_files = []
                if Path(result['project_dir']).exists():
                    for item in Path(result['project_dir']).rglob("*"):
                        if item.is_file() and item.name not in ["GEMINI.md", "brainstorm-output.log", "INSTRUCTIONS.md", ".cursorrules"]:
                            if not item.name.endswith(".json") or ".gemini" not in str(item):
                                created_files.append(item)
                
                if created_files:
                    console.print(f"[#22d3ee]✓ {len(created_files)} files created[/]")
                    console.print()
                    console.print("[#9ca3af]Would you like to:[/]")
                    console.print("  [#6b7280]1. Continue manually in the project directory[/]")
                    console.print("  [#6b7280]2. Retry with Gemini API (more stable)[/]")
                    console.print("  [#6b7280]3. Accept partial results[/]")
                else:
                    console.print("[#ef4444]No files created. Consider retrying with API method.[/]")
            else:
                console.print("[bold #22c55e]Done.[/]")
            
            console.print(f"[#9ca3af]Project: {result['project_dir']}[/]")
        else:
            console.print()
            console.print(f"[#ef4444]Execution failed: {result.get('error', 'Unknown')}[/]")
            
            # Offer fallback to API
            if check_gemini_cli():
                console.print()
                console.print("[#eab308]Retry with Gemini API instead? (More stable, no shell execution)[/]")
                if questionary.confirm("Use API fallback?", default=True, style=PROMPT_STYLE).ask():
                    console.print()
                    console.print("[#22d3ee]Retrying with Gemini API...[/]")
                    result = execute_with_api(prompt, project_dir)
                    if result.get("success"):
                        files_written = result.get("files_written", [])
                        if files_written:
                            console.print()
                            console.print(f"[#22c55e]✓ Successfully created {len(files_written)} files via API[/]")
                    else:
                        console.print(f"[#ef4444]API fallback also failed: {result.get('error')}[/]")

    elif exec_method == "api":
        # Initialize project directory with skills
        initialize_project_dir(project_dir, skills, agent_skills, mcps, gemini_kit_agent)
        
        result = execute_with_api(prompt, project_dir)
        if result.get("success"):
            files_written = result.get("files_written", [])
            if files_written:
                console.print()
                console.print(f"[#22c55e]✓ Successfully created {len(files_written)} files[/]")
                post_execution(project_dir, files_written)
            else:
                # Show the response since no files were extracted
                console.print()
                console.print("[#eab308]⚠ No code files extracted from response.[/]")
                console.print(Rule("[bold #7c3aed]Response[/]", style="#4b5563"))
                console.print()
                content = result.get("content", "")
                if content:
                    console.print(Markdown(content[:2000]))  # Show first 2000 chars
                    if len(content) > 2000:
                        console.print(f"\n[#9ca3af]... (truncated, full output in brainstorm-output.md)[/]")
                console.print(f"\n[#9ca3af]Full output saved to: {project_dir / 'brainstorm-output.md'}[/]")
        else:
            console.print()
            console.print(f"[#ef4444]API execution failed: {result.get('error', 'Unknown')}[/]")
            console.print("[#9ca3af]Check your GEMINI_API_KEY and network connection.[/]")

    console.print()
    console.print("[#4b5563]---[/]")
    console.print("[#9ca3af]brainstorm cli[/]")
    console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print()
        console.print()
        console.print("[#eab308]⚠ Interrupted by user (Ctrl+C)[/]")
        console.print("[#9ca3af]Any work in progress has been saved to the project directory.[/]")
        sys.exit(0)
    except Exception as e:
        console.print()
        console.print()
        console.print(f"[#ef4444]✗ Unexpected error: {e}[/]")
        console.print(f"[#9ca3af]Error type: {type(e).__name__}[/]")
        
        # Try to save error state
        try:
            error_file = DEV_DIR / "brainstorm-error.log"
            import traceback
            error_details = f"""Brainstorm CLI Error Report
Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
Error: {e}
Type: {type(e).__name__}

Traceback:
{traceback.format_exc()}
"""
            error_file.write_text(error_details, encoding="utf-8")
            console.print(f"[#9ca3af]Error details saved to: {error_file}[/]")
        except Exception:
            pass
        
        console.print()
        console.print("[#9ca3af]If this persists:[/]")
        console.print("  [#6b7280]1. Check your Gemini API key is set correctly[/]")
        console.print("  [#6b7280]2. Ensure bash/Git Bash is installed (Windows)[/]")
        console.print("  [#6b7280]3. Update dependencies: pip install -r requirements.txt[/]")
        console.print("  [#6b7280]4. Check the error log above for details[/]")
        console.print()
        sys.exit(1)
