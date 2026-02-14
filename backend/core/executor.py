"""
Executor — sends optimized prompts to the chosen model and handles tool use loops.
Supports both Gemini (google-genai) and Claude (anthropic) SDKs.
Handles errors gracefully with automatic fallback.
"""
import json
import re
import traceback
from pathlib import Path
from typing import Optional

from rich.console import Console

from backend.config import get_api_keys, ModelConfig

console = Console()


async def execute_prompt(
    prompt: str,
    model: str,
    provider: str,
    fallback_model: str = None,
    tools: Optional[list] = None,
    project_folder: Optional[str] = None,
) -> dict:
    """
    Send the optimized prompt to the chosen model.
    Returns dict with: content, model_used, tool_calls_made, files_created
    """
    try:
        if provider == "claude":
            result = await _execute_claude(prompt, model, tools, project_folder)
        else:
            result = await _execute_gemini(prompt, model, tools, project_folder)

        return result

    except Exception as e:
        console.print(f"[red]Primary model ({model}) failed: {e}[/red]")

        # Try fallback
        if fallback_model and fallback_model != model:
            console.print(f"[yellow]Falling back to {fallback_model}...[/yellow]")
            try:
                result = await _execute_gemini(prompt, fallback_model, tools, project_folder)
                result["fallback_used"] = True
                return result
            except Exception as e2:
                console.print(f"[red]Fallback model also failed: {e2}[/red]")

        return {
            "content": f"I encountered an error processing your request. Please try again.\n\nError: {str(e)}",
            "model_used": model,
            "tool_calls_made": [],
            "files_created": [],
            "error": str(e),
        }


async def _execute_gemini(
    prompt: str,
    model: str,
    tools: Optional[list] = None,
    project_folder: Optional[str] = None,
) -> dict:
    """Execute prompt using Google Gemini."""
    from google import genai

    keys = get_api_keys()
    if not keys.gemini_api_key:
        raise ValueError("Gemini API key not configured")

    client = genai.Client(api_key=keys.gemini_api_key)

    config = genai.types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=8192,
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    content = response.text or ""

    # Extract and write files if project folder exists
    files_created = []
    if project_folder:
        files_created = _extract_and_write_files(content, project_folder)

    return {
        "content": content,
        "model_used": model,
        "tool_calls_made": [],
        "files_created": files_created,
    }


async def _execute_claude(
    prompt: str,
    model: str,
    tools: Optional[list] = None,
    project_folder: Optional[str] = None,
) -> dict:
    """Execute prompt using Anthropic Claude."""
    import anthropic

    keys = get_api_keys()
    if not keys.anthropic_api_key:
        raise ValueError("Claude API key not configured")

    client = anthropic.Anthropic(api_key=keys.anthropic_api_key)

    message = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    # Extract text content from response
    content = ""
    for block in message.content:
        if hasattr(block, 'text'):
            content += block.text

    # Extract and write files if project folder exists
    files_created = []
    if project_folder:
        files_created = _extract_and_write_files(content, project_folder)

    return {
        "content": content,
        "model_used": model,
        "tool_calls_made": [],
        "files_created": files_created,
    }


def _extract_and_write_files(content: str, project_folder: str) -> list[str]:
    """
    Parse code blocks from AI response and write them to the project folder.
    Looks for patterns like:
    - ```filename.ext or ```language:filename.ext
    - <!-- filename: path/to/file.ext -->
    - # File: path/to/file.ext
    """
    files_created = []
    folder = Path(project_folder)
    folder.mkdir(parents=True, exist_ok=True)

    # Pattern 1: Code blocks with filenames
    # Matches: ```python:filename.py, ```filename.py, or filename preceded by a comment line
    code_block_pattern = re.compile(
        r'(?:^|\n)(?:#+ )?(?:File|file|Filename|filename)[:\s]+([^\n]+\.[\w]+)\s*\n'
        r'```[\w]*\n(.*?)```',
        re.DOTALL
    )

    for match in code_block_pattern.finditer(content):
        filepath = match.group(1).strip().strip('`').strip('"').strip("'")
        code = match.group(2)

        if filepath and code and not filepath.startswith('http'):
            try:
                target = folder / filepath
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(code, encoding="utf-8")
                files_created.append(filepath)
                console.print(f"[green]  📄 Created: {filepath}[/green]")
            except Exception as e:
                console.print(f"[yellow]  ⚠ Failed to write {filepath}: {e}[/yellow]")

    # Pattern 2: Look for explicit file creation markers
    explicit_pattern = re.compile(
        r'<!-- create:([^\n]+) -->\s*\n```[\w]*\n(.*?)```',
        re.DOTALL
    )

    for match in explicit_pattern.finditer(content):
        filepath = match.group(1).strip()
        code = match.group(2)

        if filepath and code and filepath not in files_created:
            try:
                target = folder / filepath
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(code, encoding="utf-8")
                files_created.append(filepath)
                console.print(f"[green]  📄 Created: {filepath}[/green]")
            except Exception as e:
                console.print(f"[yellow]  ⚠ Failed to write {filepath}: {e}[/yellow]")

    return files_created
