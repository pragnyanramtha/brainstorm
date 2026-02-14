"""
Model router — decides which model to use and handles fallbacks.
"""
from typing import Optional
from pydantic import BaseModel
from rich.console import Console

from backend.config import get_api_keys, ModelConfig

console = Console()


class ModelSelection(BaseModel):
    primary_model: str
    fallback_model: str
    provider: str  # "gemini" or "claude"


def select_model(
    task_type: str,
    complexity: int,
    recommended: str = "gemini",
) -> ModelSelection:
    """
    Select the best model based on task type, complexity, and available API keys.

    Decision logic:
    - Code/debugging/system_design/math → Claude Sonnet (if available), fallback Gemini
    - Creative/writing/research/analysis → Gemini (Flash or Pro based on complexity)
    - Complexity >= 8 → upgrade to best available
    - No Claude key → everything goes to Gemini
    """
    keys = get_api_keys()
    claude_available = bool(keys.anthropic_api_key)
    gemini_available = bool(keys.gemini_api_key)

    code_tasks = {"code", "debugging", "system_design", "math"}

    # Default: Gemini Flash
    primary = ModelConfig.GEMINI_FLASH
    fallback = ModelConfig.GEMINI_FLASH
    provider = "gemini"

    if task_type in code_tasks and claude_available:
        primary = ModelConfig.CLAUDE_SONNET
        fallback = ModelConfig.GEMINI_FLASH
        provider = "claude"
    elif task_type in ("creative", "writing", "research", "analysis", "conversation", "data"):
        if complexity >= 7:
            primary = ModelConfig.GEMINI_PRO
        else:
            primary = ModelConfig.GEMINI_FLASH
        fallback = ModelConfig.GEMINI_FLASH
        provider = "gemini"

    # Upgrade for high complexity
    if complexity >= 8:
        if claude_available:
            primary = ModelConfig.CLAUDE_SONNET
            provider = "claude"
            fallback = ModelConfig.GEMINI_PRO if gemini_available else ModelConfig.GEMINI_FLASH
        elif gemini_available:
            primary = ModelConfig.GEMINI_PRO
            fallback = ModelConfig.GEMINI_FLASH

    # If no Claude key, everything goes to Gemini
    if not claude_available and provider == "claude":
        primary = ModelConfig.GEMINI_PRO if complexity >= 7 else ModelConfig.GEMINI_FLASH
        fallback = ModelConfig.GEMINI_FLASH
        provider = "gemini"

    # Override with recommended if it's different and makes sense
    if recommended == "claude" and claude_available and provider != "claude":
        primary = ModelConfig.CLAUDE_SONNET
        provider = "claude"
    elif recommended == "gemini" and provider == "claude" and task_type not in code_tasks:
        primary = ModelConfig.GEMINI_PRO if complexity >= 7 else ModelConfig.GEMINI_FLASH
        provider = "gemini"

    console.print(f"[blue]Model selected: {primary} ({provider}), fallback: {fallback}[/blue]")

    return ModelSelection(
        primary_model=primary,
        fallback_model=fallback,
        provider=provider,
    )
