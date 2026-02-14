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

        # Track clarification answers across rounds (for brainstorming flow)
        pending_clarification_answers = None

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
                    if update["type"] == "message" and update["role"] == "assistant":
                        # Persist first to generate ID
                        msg = await save_message(
                            role="assistant",
                            content=update["content"],
                            metadata=update.get("metadata")
                        )
                        update["id"] = msg.id
                    
                    # Forward to frontend (now with ID for messages)
                    await websocket.send_json(update)
                    
                    # If clarification needed, save it (optional, but good for history)
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

                # Store answers for potential approach proposal phase
                pending_clarification_answers = answers

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

                        # Save approach proposal to history
                        if update["type"] == "approach_proposal":
                            await save_message(
                                role="system",
                                content="Approach proposals generated",
                                msg_type="approach_proposal",
                                metadata={
                                    "approaches": update["approaches"],
                                    "context_summary": update.get("context_summary", ""),
                                }
                            )

            # Handle approach selection (brainstorming flow)
            elif data.get("type") == "approach_selection":
                selected_approach = data.get("approach", {})
                answers = data.get("clarification_answers", pending_clarification_answers or {})

                # Save selection
                await save_message(
                    role="user",
                    content=json.dumps({"selected_approach": selected_approach.get("title", "")}),
                    msg_type="approach_selection"
                )

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
                        selected_approach=selected_approach,
                    ):
                        await websocket.send_json(update)

                        if update["type"] == "message" and update["role"] == "assistant":
                            await save_message(
                                role="assistant",
                                content=update["content"],
                                metadata=update.get("metadata")
                            )

                # Reset brainstorming state
                pending_clarification_answers = None

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
    selected_approach = payload.get("selected_approach")

    if not content and not answers and not selected_approach:
        raise HTTPException(status_code=400, detail="Content, answers, or approach selection required")

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
        selected_approach=selected_approach,
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
