"""
Project management routes.
CRUD operations for creating, listing, and archiving projects.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from pathlib import Path

from backend.database import get_session, Project, Message
from backend.utils.helpers import generate_id, slugify_name

DEV_DIR = Path.home() / "dev"

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class MessageSchema(BaseModel):
    id: str
    project_id: str
    role: str
    content: str
    message_type: str
    metadata: Optional[dict] = None
    created_at: str

    class Config:
        orm_mode = True


class ProjectSchema(BaseModel):
    id: str
    name: str
    folder_path: str
    summary: Optional[str] = None
    message_count: int
    created_at: str
    updated_at: str
    archived: bool
    messages: Optional[List[MessageSchema]] = None

    class Config:
        orm_mode = True


@router.get("", response_model=List[ProjectSchema])
async def list_projects(
    archived: bool = Query(False, description="Include archived projects"),
    session: AsyncSession = Depends(get_session),
):
    """List all projects."""
    query = select(Project).order_by(Project.updated_at.desc())
    if not archived:
        query = query.where(Project.archived == False)
    
    result = await session.execute(query)
    projects = result.scalars().all()
    
    return [p.to_dict() for p in projects]


@router.post("", response_model=ProjectSchema)
async def create_project(
    data: ProjectCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new project."""
    project_id = generate_id()
    slug = slugify_name(data.name)
    folder_path = DEV_DIR / slug
    
    # Ensure unique folder path
    counter = 1
    while folder_path.exists():
        folder_path = DEV_DIR / f"{slug}-{counter}"
        counter += 1
    
    folder_path.mkdir(parents=True, exist_ok=True)
    
    new_project = Project(
        id=project_id,
        name=data.name,
        folder_path=str(folder_path),
        summary=data.description,
    )
    
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    
    return new_project.to_dict()


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a project with messages."""
    query = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.messages))
    )
    result = await session.execute(query)
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return project.to_dict(include_messages=True)


@router.put("/{project_id}", response_model=ProjectSchema)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update project metadata."""
    query = select(Project).where(Project.id == project_id)
    result = await session.execute(query)
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if data.name:
        project.name = data.name
    if data.description:
        project.summary = data.description
        
    await session.commit()
    await session.refresh(project)
    
    return project.to_dict()


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Archive a project (soft delete)."""
    query = select(Project).where(Project.id == project_id)
    result = await session.execute(query)
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project.archived = True
    await session.commit()
    
    return {"status": "archived"}
