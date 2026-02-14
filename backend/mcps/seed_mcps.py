"""
Seeds the database with default MCP server configurations.
"""
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import MCPServer


SEED_MCPS = [
    {
        "name": "filesystem",
        "description": "Read, write, and manage files in the project workspace",
        "category": "filesystem",
        "command": "npx",
        "args": json.dumps(["-y", "@modelcontextprotocol/server-filesystem", "{workspace_path}"]),
        "env_vars": json.dumps({}),
        "capabilities": json.dumps(["file_read", "file_write", "directory_list", "file_search"]),
        "trigger_task_types": json.dumps(["code", "system_design"]),
        "trigger_keywords": json.dumps(["file", "read", "write", "save", "create", "project"]),
        "requires_user_config": False,
        "enabled": True,
        "priority": 1,
    },
    {
        "name": "github",
        "description": "Interact with GitHub repositories, issues, and pull requests",
        "category": "code_tools",
        "command": "npx",
        "args": json.dumps(["-y", "@modelcontextprotocol/server-github"]),
        "env_vars": json.dumps({"GITHUB_PERSONAL_ACCESS_TOKEN": "GitHub Personal Access Token with repo access"}),
        "capabilities": json.dumps(["repo_read", "repo_write", "issues", "pull_requests"]),
        "trigger_task_types": json.dumps(["code", "debugging"]),
        "trigger_keywords": json.dumps(["github", "repo", "commit", "PR", "issue"]),
        "requires_user_config": True,
        "enabled": False,
        "priority": 3,
    },
    {
        "name": "brave-search",
        "description": "Search the web using Brave Search API",
        "category": "search",
        "command": "npx",
        "args": json.dumps(["-y", "@modelcontextprotocol/server-brave-search"]),
        "env_vars": json.dumps({"BRAVE_API_KEY": "Brave Search API key"}),
        "capabilities": json.dumps(["web_search"]),
        "trigger_task_types": json.dumps(["research"]),
        "trigger_keywords": json.dumps(["search", "find", "latest", "current", "look up"]),
        "requires_user_config": True,
        "enabled": False,
        "priority": 4,
    },
    {
        "name": "postgres",
        "description": "Query and inspect PostgreSQL databases",
        "category": "data",
        "command": "npx",
        "args": json.dumps(["-y", "@modelcontextprotocol/server-postgres", "{connection_string}"]),
        "env_vars": json.dumps({"DATABASE_URL": "PostgreSQL connection string (postgresql://user:pass@host:port/db)"}),
        "capabilities": json.dumps(["sql_query", "schema_inspect"]),
        "trigger_task_types": json.dumps(["data", "analysis"]),
        "trigger_keywords": json.dumps(["database", "SQL", "query", "table", "postgres"]),
        "requires_user_config": True,
        "enabled": False,
        "priority": 5,
    },
    {
        "name": "memory",
        "description": "Persistent memory storage for maintaining context across sessions",
        "category": "productivity",
        "command": "npx",
        "args": json.dumps(["-y", "@modelcontextprotocol/server-memory"]),
        "env_vars": json.dumps({}),
        "capabilities": json.dumps(["persistent_memory"]),
        "trigger_task_types": json.dumps([]),
        "trigger_keywords": json.dumps(["remember", "recall", "last time"]),
        "requires_user_config": False,
        "enabled": True,
        "priority": 2,
    },
    {
        "name": "puppeteer",
        "description": "Browse URLs, take screenshots, and extract page content",
        "category": "search",
        "command": "npx",
        "args": json.dumps(["-y", "@modelcontextprotocol/server-puppeteer"]),
        "env_vars": json.dumps({}),
        "capabilities": json.dumps(["browse_url", "screenshot", "page_content"]),
        "trigger_task_types": json.dumps(["research", "data"]),
        "trigger_keywords": json.dumps(["website", "URL", "browse", "screenshot", "scrape"]),
        "requires_user_config": False,
        "enabled": False,
        "priority": 6,
    },
]


async def seed_mcps(session: AsyncSession):
    """Seed MCP servers table if empty."""
    result = await session.execute(select(MCPServer).limit(1))
    if result.scalars().first() is not None:
        return  # Already seeded

    for mcp_data in SEED_MCPS:
        mcp = MCPServer(**mcp_data)
        session.add(mcp)

    await session.commit()
