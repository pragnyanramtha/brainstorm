"""
Project CRUD routes.
"""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import WORKSPACE_DIR
from backend.database import get_session, Project, Message
from backend.utils.helpers import generate_id, slugify

router = APIRouter(tags=["projects"])


@router.get("/projects")
async def list_projects(session: AsyncSession = Depends(get_session)):
    """Return all non-archived projects sorted by updated_at desc."""
    result = await session.execute(
        select(Project).where(Project.archived == False).order_by(Project.updated_at.desc())
    )
    projects = result.scalars().all()
    return [p.to_dict() for p in projects]


@router.post("/projects")
async def create_project(body: dict = None, session: AsyncSession = Depends(get_session)):
    """Create a new project with an empty folder."""
    body = body or {}
    name = body.get("name", "New Project")
    project_id = generate_id()
    folder_name = f"{slugify(name)}_{project_id[:8]}"
    folder_path = WORKSPACE_DIR / folder_name

    folder_path.mkdir(parents=True, exist_ok=True)

    project = Project(
        id=project_id,
        name=name,
        folder_path=str(folder_path),
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)

    return project.to_dict()


@router.get("/projects/{project_id}")
async def get_project(project_id: str, session: AsyncSession = Depends(get_session)):
    """Return project details with messages."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get messages
    msg_result = await session.execute(
        select(Message).where(Message.project_id == project_id).order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    project_dict = project.to_dict()
    project_dict["messages"] = [m.to_dict() for m in messages]
    return project_dict


@router.delete("/projects/{project_id}")
async def archive_project(project_id: str, session: AsyncSession = Depends(get_session)):
    """Archive a project (soft delete)."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.archived = True
    await session.commit()

    return {"status": "archived", "id": project_id}


@router.put("/projects/{project_id}")
async def update_project(project_id: str, body: dict, session: AsyncSession = Depends(get_session)):
    """Update project name."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if "name" in body:
        project.name = body["name"]
    await session.commit()
    await session.refresh(project)

    return project.to_dict()
