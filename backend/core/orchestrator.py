"""
Main pipeline orchestrator — ties all core components together.
"""
from typing import Optional


async def process_message(
    project_id: str,
    user_message: str,
    websocket=None,
) -> dict:
    """
    Stub: Will be implemented in Task 2. Full pipeline:
    1. Load user profile → 2. Load core memories → 3. Load project context
    4. INTAKE → 5. CLARIFY (if needed) → 6. SKILL ENGINE → 7. MCP SELECTOR
    8. MODEL ROUTER → 9. OPTIMIZER → 10. EXECUTOR → 11. Save to DB
    12. MEMORY EXTRACTION → 13. Return response
    """
    return {
        "content": f"[Stub orchestrator] Processing: {user_message[:100]}...",
        "metadata": {},
    }
