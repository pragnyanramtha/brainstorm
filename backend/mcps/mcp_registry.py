"""
MCP server registry and connection management.
Handles connecting to and managing MCP server processes.
"""
import json
import asyncio
import traceback
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from rich.console import Console

from backend.database import MCPServer, UserMCPConfig
from backend.config import WORKSPACE_DIR

console = Console()

# In-memory cache of connected MCP clients
_active_connections: dict[str, any] = {}


async def get_mcp_registry(session: AsyncSession) -> list[dict]:
    """Get all registered MCP servers."""
    try:
        result = await session.execute(select(MCPServer))
        servers = result.scalars().all()
        return [s.to_dict() for s in servers]
    except Exception as e:
        console.print(f"[red]Failed to load MCP registry: {e}[/red]")
        return []


async def get_enabled_mcps(session: AsyncSession) -> list[dict]:
    """Get only enabled MCP servers."""
    try:
        result = await session.execute(
            select(MCPServer).where(MCPServer.enabled == True)
        )
        servers = result.scalars().all()
        return [s.to_dict() for s in servers]
    except Exception as e:
        console.print(f"[red]Failed to load enabled MCPs: {e}[/red]")
        return []


async def update_mcp_status(
    mcp_id: int,
    status: str,
    session: AsyncSession,
):
    """Update health status of an MCP server."""
    try:
        result = await session.execute(
            select(MCPServer).where(MCPServer.id == mcp_id)
        )
        mcp = result.scalars().first()
        if mcp:
            mcp.health_status = status
            await session.commit()
    except Exception as e:
        console.print(f"[red]Failed to update MCP status: {e}[/red]")


async def toggle_mcp(
    mcp_id: int,
    enabled: bool,
    session: AsyncSession,
) -> dict:
    """Enable or disable an MCP server."""
    try:
        result = await session.execute(
            select(MCPServer).where(MCPServer.id == mcp_id)
        )
        mcp = result.scalars().first()
        if not mcp:
            return {"error": "MCP server not found"}

        mcp.enabled = enabled
        await session.commit()
        await session.refresh(mcp)

        console.print(f"[blue]MCP '{mcp.name}' {'enabled' if enabled else 'disabled'}[/blue]")
        return mcp.to_dict()

    except Exception as e:
        console.print(f"[red]Failed to toggle MCP: {e}[/red]")
        return {"error": str(e)}


async def save_mcp_config(
    mcp_id: int,
    env_values: dict,
    session: AsyncSession,
) -> dict:
    """Save user configuration for an MCP server."""
    try:
        # Check if config already exists
        result = await session.execute(
            select(UserMCPConfig).where(UserMCPConfig.mcp_id == mcp_id)
        )
        config = result.scalars().first()

        if config:
            config.user_env_values = json.dumps(env_values)
            config.enabled = True
        else:
            config = UserMCPConfig(
                mcp_id=mcp_id,
                user_env_values=json.dumps(env_values),
                enabled=True,
            )
            session.add(config)

        await session.commit()
        console.print(f"[green]MCP config saved for ID {mcp_id}[/green]")
        return {"status": "saved"}

    except Exception as e:
        console.print(f"[red]Failed to save MCP config: {e}[/red]")
        return {"error": str(e)}


def resolve_mcp_args(args: list, project_folder: str = None) -> list:
    """Resolve template variables in MCP args."""
    workspace = str(WORKSPACE_DIR)
    resolved = []
    for arg in args:
        if isinstance(arg, str):
            arg = arg.replace("{workspace_path}", workspace)
            if project_folder:
                arg = arg.replace("{project_path}", project_folder)
            arg = arg.replace("{connection_string}", "")  # Will be filled from user config
        resolved.append(arg)
    return resolved
