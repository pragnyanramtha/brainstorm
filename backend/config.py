"""
Settings, paths, constants, and API key management for Brainstorm AI.
"""
import os
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv


# --- Path Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_DIR = Path(__file__).parent.resolve()
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
DB_PATH = WORKSPACE_DIR / ".brainstorm.db"
ENV_PATH = WORKSPACE_DIR / ".env"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"

# Ensure workspace exists
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


# --- Load environment variables ---
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
if (PROJECT_ROOT / ".env").exists():
    load_dotenv(PROJECT_ROOT / ".env")


# --- API Configuration ---
class APIKeys(BaseModel):
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None


def get_api_keys() -> APIKeys:
    return APIKeys(
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
    )


def save_api_keys(gemini_key: Optional[str] = None, anthropic_key: Optional[str] = None):
    env_lines = []
    if ENV_PATH.exists():
        env_lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    new_lines = []
    gemini_set = False
    anthropic_set = False

    for line in env_lines:
        if line.startswith("GEMINI_API_KEY="):
            if gemini_key is not None:
                new_lines.append(f"GEMINI_API_KEY={gemini_key}")
                gemini_set = True
            else:
                new_lines.append(line)
                gemini_set = True
        elif line.startswith("ANTHROPIC_API_KEY="):
            if anthropic_key is not None:
                new_lines.append(f"ANTHROPIC_API_KEY={anthropic_key}")
                anthropic_set = True
            else:
                new_lines.append(line)
                anthropic_set = True
        else:
            new_lines.append(line)

    if not gemini_set:
        new_lines.append(f"GEMINI_API_KEY={gemini_key or ''}")
    if not anthropic_set:
        new_lines.append(f"ANTHROPIC_API_KEY={anthropic_key or ''}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Reload environment
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key


def mask_key(key: Optional[str]) -> Optional[str]:
    if not key or len(key) < 8:
        return None
    return f"{key[:4]}...{key[-6:]}"


# --- Model Configuration ---
class ModelConfig:
    GEMINI_FLASH = "gemini-3-flash-preview"
    GEMINI_PRO = "gemini-3-pro-preview"
    CLAUDE_SONNET = "claude-sonnet-4-20250514"

    INTAKE_MODEL = GEMINI_FLASH
    CLARIFIER_MODEL = GEMINI_FLASH
    OPTIMIZER_MODEL = GEMINI_FLASH
    MEMORY_MODEL = GEMINI_FLASH

    MAX_TOOL_ITERATIONS = 10
    MAX_CLARIFICATION_ROUNDS = 2
    CONFIDENCE_THRESHOLD = 85

    MAX_CORE_MEMORIES = 20
    MAX_MESSAGES_CONTEXT = 20


# --- Server Configuration ---
class ServerConfig:
    HOST = "0.0.0.0"
    PORT = 3847
    DEV_FRONTEND_PORT = 5173
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3847",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3847",
    ]


# --- Database Configuration ---
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
