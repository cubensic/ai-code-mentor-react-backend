from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.api.auth import verify_clerk_token
from app.models.chat import ChatMessage
from app.models.project import Project
from app.models.file import File
from app.schemas.chat import ChatMessage as ChatMessageSchema, ChatRequest
from app.services.openai_service import openai_service
from app.services.rate_limiter import check_rate_limit
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/stream")
async def stream_chat(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Stream AI response with context"""
    # Get or create database user
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",
        username=None
    )
    
    # Verify project exists
    project_query = select(Project).where(Project.id == chat_request.project_id)
    project_result = await db.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify project belongs to user
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check rate limit (use database user ID)
    can_proceed, remaining = await check_rate_limit(db, user.id)
    if not can_proceed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. You've used all {remaining} prompts this hour."
        )
    
    # Get project files for context
    files_query = select(File).where(File.project_id == chat_request.project_id)
    files_result = await db.execute(files_query)
    files = files_result.scalars().all()
    
    # Convert files to dict format
    files_context = [
        {
            "name": file.name,
            "file_type": file.file_type,
            "content": file.content or ""
        }
        for file in files
    ]
    
    # Get chat history
    history_query = select(ChatMessage).where(
        ChatMessage.project_id == chat_request.project_id
    ).order_by(ChatMessage.created_at.asc()).limit(20)
    
    history_result = await db.execute(history_query)
    history_messages = history_result.scalars().all()
    
    # Convert history to OpenAI format
    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_messages
    ]
    
    # Save user message
    user_message = ChatMessage(
        project_id=chat_request.project_id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    await db.commit()
    
    # Stream response
    return await openai_service.stream_response(
        template_type=project.template_type,
        user_message=chat_request.message,
        files_context=files_context or chat_request.files_context or [],
        chat_history=chat_history
    )

@router.get("/history/{project_id}", response_model=List[ChatMessageSchema])
async def get_chat_history(
    project_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Get chat history for project"""
    # Get or create database user
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",
        username=None
    )
    
    # Verify project exists
    project_query = select(Project).where(Project.id == project_id)
    project_result = await db.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify project belongs to user
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get messages
    query = select(ChatMessage).where(
        ChatMessage.project_id == project_id
    ).order_by(ChatMessage.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return list(reversed(messages))  # Return in chronological order

@router.post("/save-assistant-message")
async def save_assistant_message(
    request: dict,
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Save assistant message to database"""
    project_id = UUID(request["project_id"])
    content = request["content"]
    
    # Get or create database user
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",
        username=None
    )
    
    # Verify project exists and belongs to user
    project_query = select(Project).where(Project.id == project_id)
    project_result = await db.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Save assistant message
    assistant_message = ChatMessage(
        project_id=project_id,
        role="assistant",
        content=content
    )
    db.add(assistant_message)
    await db.commit()
    
    return {"status": "saved"}

@router.post("/initial-message")
async def get_initial_message(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Get initial AI greeting based on template"""
    # Get or create database user
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",
        username=None
    )
    
    # Get project
    project_query = select(Project).where(Project.id == project_id)
    project_result = await db.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify project belongs to user
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    message = openai_service.get_initial_message(project.template_type)
    
    return {"message": message}