"""
SQLAlchemy setup, engine, async session, and all table models for Brainstorm AI.
"""
import datetime
import json
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
    create_engine, event,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship

from backend.config import DATABASE_URL, DB_PATH


# --- Async Engine & Session ---
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


# --- Base ---
class Base(DeclarativeBase):
    pass


# --- JSON helper: SQLite stores JSON as TEXT ---
class JSONColumn(Text):
    """Marker type for documentation; stored as TEXT, serialized/deserialized in code."""
    pass


def _now():
    return datetime.datetime.utcnow()


# --- Table Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, default=1)
    technical_level = Column(String, default="semi_technical")  # non_technical | semi_technical | technical | expert
    domain = Column(String, default="")
    role = Column(String, default="")
    stack = Column(Text, default="[]")  # JSON list
    communication_preferences = Column(Text, default='{"detail_level": "balanced", "tone": "friendly", "format": "markdown"}')
    pet_peeves = Column(Text, default="[]")  # JSON list
    positive_patterns = Column(Text, default="[]")  # JSON list
    interaction_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    def get_stack(self):
        return json.loads(self.stack) if self.stack else []

    def set_stack(self, value):
        self.stack = json.dumps(value)

    def get_communication_preferences(self):
        return json.loads(self.communication_preferences) if self.communication_preferences else {}

    def set_communication_preferences(self, value):
        self.communication_preferences = json.dumps(value)

    def get_pet_peeves(self):
        return json.loads(self.pet_peeves) if self.pet_peeves else []

    def set_pet_peeves(self, value):
        self.pet_peeves = json.dumps(value)

    def get_positive_patterns(self):
        return json.loads(self.positive_patterns) if self.positive_patterns else []

    def set_positive_patterns(self, value):
        self.positive_patterns = json.dumps(value)

    def to_dict(self):
        return {
            "id": self.id,
            "technical_level": self.technical_level,
            "domain": self.domain,
            "role": self.role,
            "stack": self.get_stack(),
            "communication_preferences": self.get_communication_preferences(),
            "pet_peeves": self.get_pet_peeves(),
            "positive_patterns": self.get_positive_patterns(),
            "interaction_count": self.interaction_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CoreMemory(Base):
    __tablename__ = "core_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String, nullable=False)  # identity | preference | project_context | technical | relationship
    content = Column(Text, nullable=False)
    source_session_id = Column(String, nullable=True)
    importance = Column(Float, default=0.5)
    created_at = Column(DateTime, default=_now)
    last_accessed = Column(DateTime, default=_now)
    access_count = Column(Integer, default=0)
    active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "content": self.content,
            "source_session_id": self.source_session_id,
            "importance": self.importance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "active": self.active,
        }


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    folder_path = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    task_types_used = Column(Text, default="[]")  # JSON list
    models_used = Column(Text, default="[]")  # JSON list
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)
    archived = Column(Boolean, default=False)

    messages = relationship("Message", back_populates="project", cascade="all, delete-orphan")

    def get_task_types_used(self):
        return json.loads(self.task_types_used) if self.task_types_used else []

    def get_models_used(self):
        return json.loads(self.models_used) if self.models_used else []

    def to_dict(self, include_messages=False):
        d = {
            "id": self.id,
            "name": self.name,
            "folder_path": self.folder_path,
            "summary": self.summary,
            "task_types_used": self.get_task_types_used(),
            "models_used": self.get_models_used(),
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "archived": self.archived,
        }
        if include_messages and self.messages:
            d["messages"] = [m.to_dict() for m in self.messages]
        return d


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    role = Column(String, nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    message_type = Column(String, default="chat")  # chat | clarification_question | clarification_answer | status
    metadata_json = Column("metadata", Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=_now)

    project = relationship("Project", back_populates="messages")

    def get_metadata(self):
        return json.loads(self.metadata_json) if self.metadata_json else {}

    def set_metadata(self, value):
        self.metadata_json = json.dumps(value)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "role": self.role,
            "content": self.content,
            "message_type": self.message_type,
            "metadata": self.get_metadata(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)  # reasoning | formatting | quality | domain
    description = Column(Text, nullable=False)
    implementation_template = Column(Text, nullable=False)
    best_for_task_types = Column(Text, default="[]")  # JSON list
    complexity_range_min = Column(Integer, default=1)
    complexity_range_max = Column(Integer, default=10)
    effectiveness_score = Column(Float, default=0.5)
    usage_count = Column(Integer, default=0)
    positive_feedback_count = Column(Integer, default=0)
    negative_feedback_count = Column(Integer, default=0)
    active = Column(Boolean, default=True)

    def get_best_for_task_types(self):
        return json.loads(self.best_for_task_types) if self.best_for_task_types else []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "implementation_template": self.implementation_template,
            "best_for_task_types": self.get_best_for_task_types(),
            "complexity_range_min": self.complexity_range_min,
            "complexity_range_max": self.complexity_range_max,
            "effectiveness_score": self.effectiveness_score,
            "usage_count": self.usage_count,
            "positive_feedback_count": self.positive_feedback_count,
            "negative_feedback_count": self.negative_feedback_count,
            "active": self.active,
        }


class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # filesystem | code_tools | search | data | communication | productivity | custom
    command = Column(String, nullable=False)
    args = Column(Text, default="[]")  # JSON list
    env_vars = Column(Text, default="{}")  # JSON dict
    capabilities = Column(Text, default="[]")  # JSON list
    trigger_task_types = Column(Text, default="[]")  # JSON list
    trigger_keywords = Column(Text, default="[]")  # JSON list
    requires_user_config = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    health_status = Column(String, default="unknown")
    priority = Column(Integer, default=5)

    user_configs = relationship("UserMCPConfig", back_populates="mcp_server", cascade="all, delete-orphan")

    def get_args(self):
        return json.loads(self.args) if self.args else []

    def get_env_vars(self):
        return json.loads(self.env_vars) if self.env_vars else {}

    def get_capabilities(self):
        return json.loads(self.capabilities) if self.capabilities else []

    def get_trigger_task_types(self):
        return json.loads(self.trigger_task_types) if self.trigger_task_types else []

    def get_trigger_keywords(self):
        return json.loads(self.trigger_keywords) if self.trigger_keywords else []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "command": self.command,
            "args": self.get_args(),
            "env_vars": self.get_env_vars(),
            "capabilities": self.get_capabilities(),
            "trigger_task_types": self.get_trigger_task_types(),
            "trigger_keywords": self.get_trigger_keywords(),
            "requires_user_config": self.requires_user_config,
            "enabled": self.enabled,
            "health_status": self.health_status,
            "priority": self.priority,
        }


class UserMCPConfig(Base):
    __tablename__ = "user_mcp_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mcp_id = Column(Integer, ForeignKey("mcp_servers.id"), nullable=False)
    user_env_values = Column(Text, default="{}")  # JSON dict
    enabled = Column(Boolean, default=True)
    configured_at = Column(DateTime, default=_now)

    mcp_server = relationship("MCPServer", back_populates="user_configs")

    def get_user_env_values(self):
        return json.loads(self.user_env_values) if self.user_env_values else {}

    def to_dict(self):
        return {
            "id": self.id,
            "mcp_id": self.mcp_id,
            "user_env_values": self.get_user_env_values(),
            "enabled": self.enabled,
            "configured_at": self.configured_at.isoformat() if self.configured_at else None,
        }


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    skills_used = Column(Text, default="[]")  # JSON list
    model_used = Column(String, nullable=True)
    created_at = Column(DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "project_id": self.project_id,
            "rating": self.rating,
            "comment": self.comment,
            "skills_used": json.loads(self.skills_used) if self.skills_used else [],
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# --- Database Initialization ---
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()
