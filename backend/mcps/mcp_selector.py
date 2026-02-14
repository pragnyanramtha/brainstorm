"""
MCP selector — decides which MCPs to activate per task.
"""
import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from rich.console import Console

from backend.database import MCPServer, UserMCPConfig

console = Console()


async def select_mcps(
    task_type: str,
    interpreted_intent: str,
    session: AsyncSession = None,
) -> dict:
    """
    Select relevant MCP servers for this task.

    Logic:
    1. Match by task_type in trigger_task_types OR keyword match in interpreted_intent
    2. Filter: only enabled AND (not requires_user_config OR has user config)
    3. Sort by priority
    4. Return: active MCPs (ready to use) + recommended MCPs (need setup)
    """
    if not session:
        return {"active": [], "recommended": []}

    try:
        # Get all MCP servers
        result = await session.execute(select(MCPServer))
        all_mcps = result.scalars().all()

        # Get user configs
        config_result = await session.execute(select(UserMCPConfig))
        user_configs = {c.mcp_id: c for c in config_result.scalars().all()}

        active = []
        recommended = []
        intent_lower = interpreted_intent.lower()

        for mcp in all_mcps:
            # Check if this MCP is relevant
            trigger_types = mcp.get_trigger_task_types()
            trigger_keywords = mcp.get_trigger_keywords()

            type_match = task_type in trigger_types if trigger_types else False
            keyword_match = any(kw.lower() in intent_lower for kw in trigger_keywords)

            if not type_match and not keyword_match:
                continue

            # Check if it's usable
            if not mcp.enabled:
                continue

            has_config = mcp.id in user_configs
            config_satisfied = not mcp.requires_user_config or has_config

            mcp_info = {
                "id": mcp.id,
                "name": mcp.name,
                "description": mcp.description,
                "capabilities": mcp.get_capabilities(),
                "priority": mcp.priority,
                "command": mcp.command,
                "args": mcp.get_args(),
            }

            if config_satisfied:
                active.append(mcp_info)
            else:
                # Would be useful but not configured
                mcp_info["needs_setup"] = True
                env_vars = mcp.get_env_vars()
                mcp_info["required_config"] = list(env_vars.keys())
                recommended.append(mcp_info)

        # Sort by priority (lower = higher priority)
        active.sort(key=lambda x: x["priority"])
        recommended.sort(key=lambda x: x["priority"])

        if active:
            console.print(f"[blue]MCPs active: {', '.join(m['name'] for m in active)}[/blue]")
        if recommended:
            console.print(f"[yellow]MCPs recommended (need setup): {', '.join(m['name'] for m in recommended)}[/yellow]")

        return {"active": active, "recommended": recommended}

    except Exception as e:
        console.print(f"[red]MCP selection failed: {e}[/red]")
        return {"active": [], "recommended": []}
