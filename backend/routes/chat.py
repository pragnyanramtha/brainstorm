"""
Chat routes — WebSocket and REST endpoints for message handling.
Connects the frontend to the orchestrator.
"""
import json
import asyncio
import traceback
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_session, Project, Message
from backend.core.orchestrator import process_message
from backend.utils.helpers import generate_id

router = APIRouter()


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str,
    session: AsyncSession = Depends(get_session),
):
    await websocket.accept()
    
    # helper to save message to DB
    async def save_message(role, content, msg_type="chat", metadata=None):
        msg = Message(
            id=generate_id(),
            project_id=project_id,
            role=role,
            content=content,
            message_type=msg_type,
        )
        if metadata:
            msg.set_metadata(metadata)
        session.add(msg)
        await session.commit()
        return msg

    try:
        # Verify project exists
        project = await session.scalar(select(Project).where(Project.id == project_id))
        if not project:
            await websocket.close(code=4004, reason="Project not found")
            return

        while True:
            data = await websocket.receive_json()
            
            # Handle user message
            if data.get("type") == "message":
                user_content = data.get("content", "")
                if not user_content:
                    continue

                # Save user message
                await save_message("user", user_content)
                
                # Get conversation context (last 20 messages) but formatted as text context if needed
                # For now, orchestrator handles context loading via core memories + project context
                # We mainly need to pass the project folder path
                
                # Process through orchestrator
                async for update in process_message(
                    user_message=user_content,
                    project_id=project_id,
                    session=session,
                    project_folder=project.folder_path,
                    project_context=project.summary or "",  # Pass summary as context
                ):
                    # Forward all updates to frontend
                    await websocket.send_json(update)
                    
                    # Persist assistant messages to DB
                    if update["type"] == "message" and update["role"] == "assistant":
                        await save_message(
                            role="assistant",
                            content=update["content"],
                            metadata=update.get("metadata")
                        )
                    
                    # If clarification needed, save it (optional, but good for history)
                    if update["type"] == "clarification":
                        await save_message(
                            role="system",
                            content="Clarification requested",
                            msg_type="clarification_question",
                            metadata={"questions": update["questions"]}
                        )

            # Handle clarification response
            elif data.get("type") == "clarification_response":
                answers = data.get("answers", {})
                
                # Save answer
                await save_message(
                    role="user",
                    content=json.dumps(answers),
                    msg_type="clarification_answer"
                )

                # Continue processing with answers
                # We need the original message likely. 
                # For simplicity in this V1, let's assume the frontend re-sends or we cache it?
                # Actually, orchestrator supports `previous_intake` logic but we need state.
                # A simpler approach for V1: treat it as a new message but with answers context.
                # BUT, to make it seamless, let's fetch the last user message.
                
                last_user_msg = await session.scalar(
                    select(Message)
                    .where(Message.project_id == project_id, Message.role == "user", Message.message_type == "chat")
                    .order_by(Message.created_at.desc())
                    .limit(1)
                )
                
                if last_user_msg:
                    async for update in process_message(
                        user_message=last_user_msg.content,
                        project_id=project_id,
                        session=session,
                        project_folder=project.folder_path,
                        project_context=project.summary,
                        clarification_answers=answers,
                    ):
                        await websocket.send_json(update)
                        
                        if update["type"] == "message" and update["role"] == "assistant":
                            await save_message(
                                role="assistant",
                                content=update["content"],
                                metadata=update.get("metadata")
                            )

    except WebSocketDisconnect:
        print(f"Client disconnected from project {project_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass


@router.post("/chat/{project_id}")
async def chat_post(
    project_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_session),
):
    """
    REST endpoint for chat (alternative to WebSocket).
    Payload: {"content": "message", "clarification_answers": {...}}
    """
    project = await session.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = payload.get("content")
    answers = payload.get("clarification_answers")

    if not content and not answers:
        raise HTTPException(status_code=400, detail="Content or answers required")

    # Save user message if new content
    if content:
        msg = Message(
            id=generate_id(),
            project_id=project_id,
            role="user",
            content=content,
        )
        session.add(msg)
        await session.commit()

    # Process
    updates = []
    async for update in process_message(
        user_message=content or "Continuing with clarification",
        project_id=project_id,
        session=session,
        project_folder=project.folder_path,
        project_context=project.summary,
        clarification_answers=answers,
    ):
        updates.append(update)
        
        # Persist assistant response
        if update["type"] == "message" and update["role"] == "assistant":
            msg = Message(
                id=generate_id(),
                project_id=project_id,
                role="assistant",
                content=update["content"],
                metadata_json=json.dumps(update.get("metadata", {}))
            )
            session.add(msg)
            await session.commit()

    return updates
