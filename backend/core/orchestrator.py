"""
Orchestrator — the main pipeline that ties everything together.

Flow:
1. Intake → analyze intent (Gemini Flash)
2. If confidence < 85 → Clarify → return questions to user → wait for answers
3. Load user profile + core memories
4. Select skills
5. Select MCPs
6. Web search (if needed)
7. Optimize → build the perfect prompt
8. Route → pick best model
9. Execute → call the model
10. Remember → extract new memories (background)
11. Return response
"""
import json
import asyncio
import traceback
from typing import AsyncGenerator, Optional

from rich.console import Console
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.intake import analyze_intent
from backend.core.clarifier import generate_clarifications, generate_approach_proposals
from backend.core.optimizer import build_optimized_prompt
from backend.core.model_router import select_model
from backend.core.executor import execute_prompt
from backend.memory.user_profile import get_user_profile, update_interaction_count
from backend.memory.core_memory import recall_memories, remember
from backend.skills.skill_engine import select_skills
from backend.mcps.mcp_selector import select_mcps
from backend.tools.web_search import should_search, search_and_summarize
from backend.tools.project_scaffolder import scaffold_project, extract_files_from_response

console = Console()

# Confidence threshold below which we ask clarifying questions
CLARIFICATION_THRESHOLD = 85


async def process_message(
    user_message: str,
    project_id: str,
    session: AsyncSession,
    project_folder: str = None,
    project_context: str = None,
    on_status: callable = None,
    clarification_answers: Optional[dict] = None,
    previous_intake: Optional[dict] = None,
    selected_approach: Optional[dict] = None,
) -> AsyncGenerator[dict, None]:
    """
    Main processing pipeline. Yields status updates and the final response.

    Yields dicts with:
    - {"type": "status", "state": "analyzing|clarifying|brainstorming|optimizing|executing|scaffolding|complete", "detail": "..."}
    - {"type": "clarification", "questions": [...]}
    - {"type": "approach_proposal", "approaches": [...]}
    - {"type": "message", "role": "assistant", "content": "...", "metadata": {...}}
    - {"type": "error", "message": "..."}
    """
    try:
        # ── STEP 1: Load user profile & memories ──
        yield {"type": "status", "state": "analyzing", "detail": "Loading your profile & memories..."}

        user_profile = await get_user_profile(session)
        core_memories = await recall_memories(
            project_id=project_id,
            session=session,
        )

        # ── STEP 2: Intent Analysis ──
        if previous_intake and clarification_answers:
            # We're continuing from clarification — merge the answers
            intake = previous_intake
            intake["confidence_score"] = 95  # Answers resolved ambiguity
        else:
            yield {"type": "status", "state": "analyzing", "detail": "Analyzing what you need..."}
            intake_result = await analyze_intent(
                user_message=user_message,
                user_profile=user_profile,
                core_memories=core_memories,
                project_context=project_context,
            )
            intake = intake_result.model_dump()

        console.print(f"[bold blue]Intake:[/bold blue] {intake['interpreted_intent']}")
        console.print(f"  Type: {intake['task_type']} | Complexity: {intake['complexity']}/10 | Confidence: {intake['confidence_score']}%")

        # ── STEP 3: Brainstorming gate & Clarification ──
        requires_brainstorming = intake.get("requires_brainstorming", False)

        if requires_brainstorming:
            # Brainstorming tasks ALWAYS go through clarification + approach proposal
            if not clarification_answers:
                # Phase 1: Ask clarifying questions (always, regardless of confidence)
                yield {"type": "status", "state": "clarifying"}

                clarification = await generate_clarifications(
                    intake_analysis=intake,
                    user_message=user_message,
                    user_profile=user_profile,
                    core_memories=core_memories,
                )

                if clarification.needs_clarification:
                    yield {
                        "type": "clarification",
                        "questions": [q.model_dump() for q in clarification.questions],
                        "_intake": intake,
                        "_brainstorming": True,
                    }
                    return

            elif not selected_approach:
                # Phase 2: Propose approaches (user answered questions but hasn't picked approach)
                yield {"type": "status", "state": "brainstorming"}

                approach_result = await generate_approach_proposals(
                    intake_analysis=intake,
                    user_message=user_message,
                    clarification_qa=clarification_answers,
                    user_profile=user_profile,
                )

                if approach_result.approaches:
                    yield {
                        "type": "approach_proposal",
                        "approaches": [a.model_dump() for a in approach_result.approaches],
                        "context_summary": approach_result.context_summary,
                        "_intake": intake,
                    }
                    return
                # If approach generation failed, continue with execution anyway

        elif intake["confidence_score"] < CLARIFICATION_THRESHOLD and not clarification_answers:
            # Non-brainstorming tasks: only clarify when confidence is low
            yield {"type": "status", "state": "clarifying"}

            clarification = await generate_clarifications(
                intake_analysis=intake,
                user_message=user_message,
                user_profile=user_profile,
                core_memories=core_memories,
            )

            if clarification.needs_clarification:
                yield {
                    "type": "clarification",
                    "questions": [q.model_dump() for q in clarification.questions],
                    "_intake": intake,
                }
                return

        # ── STEP 4: Select skills ──
        yield {"type": "status", "state": "optimizing", "detail": "Selecting skills for this task..."}

        selected_skills = await select_skills(
            task_type=intake["task_type"],
            complexity=intake["complexity"],
            user_profile=user_profile,
            session=session,
        )

        # ── STEP 5: Select MCPs ──
        yield {"type": "status", "state": "optimizing", "detail": "Checking available tools..."}
        mcp_selection = await select_mcps(
            task_type=intake["task_type"],
            interpreted_intent=intake["interpreted_intent"],
            session=session,
        )

        # ── STEP 6: Web search (if needed) ──
        search_context = None
        if should_search(intake["interpreted_intent"], intake["task_type"], user_message):
            yield {"type": "status", "state": "optimizing", "detail": "Searching the web for context..."}
            console.print("[blue]Running web search...[/blue]")
            search_context = await search_and_summarize(user_message[:200])

        # ── STEP 7: Build optimized prompt ──
        yield {"type": "status", "state": "optimizing", "detail": "Crafting the perfect prompt..."}
        # Build clarification Q&A pairs if we have answers
        clarification_qa = None
        if clarification_answers:
            clarification_qa = [
                {"question": q, "answer": a}
                for q, a in clarification_answers.items()
            ]

        # Combine project context with search context
        full_context = ""
        if project_context:
            full_context += project_context
        if search_context:
            full_context += "\n\n" + search_context if full_context else search_context

        optimized_prompt = await build_optimized_prompt(
            user_message=user_message,
            intake_analysis=intake,
            clarification_qa=clarification_qa,
            user_profile=user_profile,
            core_memories=core_memories,
            selected_skills=selected_skills,
            available_tools=mcp_selection.get("active", []),
            project_context=full_context or None,
            selected_approach=selected_approach,
        )

        # ── STEP 8: Route to model ──
        model_selection = select_model(
            task_type=intake["task_type"],
            complexity=intake["complexity"],
            recommended=intake.get("recommended_model", "gemini"),
        )

        # ── STEP 9: Execute ──
        yield {"type": "status", "state": "executing", "detail": f"Sending to {model_selection.primary_model}..."}

        result = await execute_prompt(
            prompt=optimized_prompt,
            model=model_selection.primary_model,
            provider=model_selection.provider,
            fallback_model=model_selection.fallback_model,
        )

        # ── STEP 9.5: Scaffold project if this was a building task ──
        scaffold_result = None
        if intake.get("requires_brainstorming") or intake["task_type"] in ("code", "creative", "system_design"):
            # Check if AI response contains file blocks worth scaffolding
            candidate_files = extract_files_from_response(result["content"])
            if candidate_files:
                # Derive project name from intent
                project_name = intake.get("interpreted_intent", "project")[:60]

                yield {"type": "status", "state": "scaffolding", "detail": f"Creating project with {len(candidate_files)} files..."}

                scaffold_result = await scaffold_project(
                    project_name=project_name,
                    ai_response=result["content"],
                )

                if scaffold_result.get("scaffolded"):
                    dev_server = scaffold_result.get("dev_server", {})
                    if dev_server and dev_server.get("running"):
                        yield {"type": "status", "state": "scaffolding", "detail": f"Dev server running at {dev_server['url']}"}
                    else:
                        yield {"type": "status", "state": "scaffolding", "detail": f"Project created at {scaffold_result['project_dir']}"}

        # ── STEP 10: Build metadata ──
        metadata = {
            "model_used": result.get("model_used", model_selection.primary_model),
            "skills_applied": [s.get("name", "") for s in selected_skills],
            "mcps_used": [m.get("name", "") for m in mcp_selection.get("active", [])],
            "confidence_score": intake["confidence_score"],
            "optimized_prompt": optimized_prompt,
            "task_type": intake["task_type"],
            "complexity": intake["complexity"],
            "interpreted_intent": intake["interpreted_intent"],
        }

        if result.get("fallback_used"):
            metadata["fallback_used"] = True

        if result.get("files_created"):
            metadata["files_created"] = result["files_created"]

        # Add scaffold metadata
        if scaffold_result and scaffold_result.get("scaffolded"):
            metadata["project_dir"] = scaffold_result["project_dir"]
            metadata["project_type"] = scaffold_result.get("project_type", "unknown")
            metadata["files_created"] = scaffold_result.get("files_created", [])
            dev_server = scaffold_result.get("dev_server", {})
            if dev_server and dev_server.get("running"):
                metadata["dev_server_url"] = dev_server["url"]
                metadata["dev_server_pid"] = dev_server.get("pid")

        # ── STEP 11: Build response content ──
        response_content = result["content"]

        # If we scaffolded, prepend a project summary instead of raw code dump
        if scaffold_result and scaffold_result.get("scaffolded"):
            project_dir = scaffold_result["project_dir"]
            files_list = scaffold_result.get("files_created", [])
            dev_server = scaffold_result.get("dev_server", {})

            project_header = f"## ✅ Project Created\n\n"
            project_header += f"**Location:** `{project_dir}`\n\n"

            if files_list:
                project_header += f"**Files created ({len(files_list)}):**\n"
                for f in files_list[:20]:
                    project_header += f"- `{f}`\n"
                if len(files_list) > 20:
                    project_header += f"- ... and {len(files_list) - 20} more\n"
                project_header += "\n"

            if dev_server and dev_server.get("running"):
                project_header += f"**🚀 Dev server running:** [{dev_server['url']}]({dev_server['url']})\n\n"
            elif dev_server and dev_server.get("error"):
                project_header += f"**⚠️ Dev server:** {dev_server['error']}\n\n"

            if not scaffold_result.get("install_success"):
                project_header += f"**⚠️ Dependencies:** Install may have had issues. Run `npm install` or `pip install -r requirements.txt` manually.\n\n"

            project_header += "---\n\n"
            response_content = project_header + response_content

        # ── STEP 12: Yield response ──
        yield {
            "type": "message",
            "role": "assistant",
            "content": response_content,
            "metadata": metadata,
        }
        yield {"type": "status", "state": "complete"}

        # ── STEP 12: Background tasks ──
        # Update interaction count
        await update_interaction_count(session)

        # Extract memories (fire and forget, don't block response)
        try:
            await remember(
                user_message=user_message,
                assistant_response=result["content"],
                project_id=project_id,
                session=session,
            )
        except Exception as e:
            console.print(f"[yellow]Background memory extraction failed: {e}[/yellow]")

        # Notify about recommended MCPs
        if mcp_selection.get("recommended"):
            names = [m["name"] for m in mcp_selection["recommended"]]
            yield {
                "type": "status",
                "state": "info",
                "message": f"💡 Enable these MCP tools for better results: {', '.join(names)}",
            }

    except Exception as e:
        console.print(f"[red]Pipeline error: {e}[/red]")
        console.print(traceback.format_exc())
        yield {
            "type": "error",
            "message": f"Something went wrong: {str(e)}",
        }
