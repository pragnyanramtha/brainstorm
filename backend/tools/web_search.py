"""
Built-in web search using DuckDuckGo (no API key needed).
Falls back gracefully if unavailable.
"""
import traceback
from typing import Optional

from rich.console import Console

console = Console()


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web using DuckDuckGo.
    Returns list of {title, url, snippet} dicts.
    Falls back gracefully if the library isn't available or search fails.
    """
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                })

        if results:
            console.print(f"[blue]Web search: {len(results)} results for '{query[:50]}'[/blue]")

        return results

    except ImportError:
        console.print("[yellow]duckduckgo-search not installed, web search unavailable[/yellow]")
        return []
    except Exception as e:
        console.print(f"[yellow]Web search failed: {e}[/yellow]")
        return []


def should_search(
    interpreted_intent: str,
    task_type: str,
    user_message: str,
) -> bool:
    """
    Determine if web search should be triggered for this task.

    Triggers when:
    - Task type is "research"
    - Keywords suggest need for current information
    - Intent analysis suggested web_search capability
    """
    if task_type == "research":
        return True

    current_keywords = [
        "latest", "current", "2024", "2025", "2026", "today", "recent",
        "news", "update", "new version", "just released", "trending",
        "what is", "how to", "best practices",
    ]

    msg_lower = user_message.lower()
    intent_lower = interpreted_intent.lower()

    return any(kw in msg_lower or kw in intent_lower for kw in current_keywords)


async def search_and_summarize(query: str, max_results: int = 5) -> Optional[str]:
    """
    Search and return a formatted summary of results.
    Used to inject search context into the optimizer.
    """
    results = await web_search(query, max_results)

    if not results:
        return None

    summary_parts = ["Web search results:"]
    for i, r in enumerate(results, 1):
        summary_parts.append(f"\n{i}. **{r['title']}** ({r['url']})")
        if r.get('snippet'):
            summary_parts.append(f"   {r['snippet']}")

    return "\n".join(summary_parts)
