"""
FastAPI application entry point for Middle Manager AI.
Handles startup, shutdown, and serves the built frontend.
"""
import os
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from rich.console import Console

from backend.config import ServerConfig, FRONTEND_DIST_DIR
from backend.database import init_db, close_db, async_session_factory
from backend.skills.seed_skills import seed_skills
from backend.mcps.seed_mcps import seed_mcps

# Import routes
from backend.routes import chat, projects, settings, debug, feedback

console = Console()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    console.print("[bold green]🚀 Starting Middle Manager AI...[/bold green]")

    # Initialize database
    await init_db()
    console.print("[green]✓[/green] Database initialized")

    # Seed data
    async with async_session_factory() as session:
        await seed_skills(session)
        await seed_mcps(session)
        console.print("[green]✓[/green] Seed data checked")

    console.print(f"[bold green]✓ Ready at http://localhost:{ServerConfig.PORT}[/bold green]")

    yield

    # Shutdown
    await close_db()
    console.print("[yellow]Shutting down...[/yellow]")


app = FastAPI(
    title="Middle Manager AI",
    description="Intelligent middleware between humans and AI models",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Include API routes ---
# chat.router has no prefix, so we add /api here
app.include_router(chat.router, prefix="/api")
# The others already have prefixes defined in their files
app.include_router(projects.router)
app.include_router(settings.router)
app.include_router(debug.router)
app.include_router(feedback.router)


# --- Serve frontend ---
# Only mount if build exists
if FRONTEND_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the React SPA — all non-API routes return index.html."""
        # Check if file exists in dist
        file_path = FRONTEND_DIST_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # Otherwise fallback to index.html
        return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=ServerConfig.HOST,
        port=ServerConfig.PORT,
        reload=True,
    )
