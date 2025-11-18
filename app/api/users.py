from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from uuid import UUID

from app.database import get_db
from app.api.auth import verify_clerk_token
from app.models.user import User
from app.schemas.user import UserResponse, RateLimitResponse
from app.services.user_service import get_or_create_user
from app.config import settings

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Get current user profile with stats. Creates user if doesn't exist."""
    # Find or create user
    # Note: For now, we'll need to get email from Clerk API or token
    # For MVP, let's try to get it from token payload, or create with placeholder
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",  # Temporary - will get from token later
        username=None
    )
    
    return user

@router.get("/rate-limit", response_model=RateLimitResponse)
async def get_rate_limit(
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Check remaining prompts and reset time"""
    # Get or create user
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",
        username=None
    )
    
    # Calculate remaining prompts
    max_prompts = settings.MAX_PROMPTS_PER_HOUR
    remaining = max(0, max_prompts - user.hourly_prompt_count)
    
    # Calculate reset time (1 hour from last reset)
    if user.last_prompt_reset:
        reset_time = user.last_prompt_reset + timedelta(hours=1)
        # If reset time is in the past, it resets now
        if reset_time < datetime.utcnow():
            reset_time = datetime.utcnow() + timedelta(hours=1)
    else:
        reset_time = datetime.utcnow() + timedelta(hours=1)
    
    return RateLimitResponse(
        remaining_prompts=remaining,
        reset_time=reset_time,
        max_prompts=max_prompts
    )