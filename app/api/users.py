from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from uuid import UUID

from app.database import get_db
from app.api.auth import verify_clerk_token
from app.models.user import User
from app.schemas.user import UserResponse, RateLimitResponse
from app.config import settings

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Get current user profile with stats"""
    # TODO: Convert user_id (Clerk ID) to database user_id
    # For now, using placeholder logic
    if user_id == "placeholder_user_id":
        raise HTTPException(status_code=404, detail="User not found")
    
    # Try to find user by clerk_user_id first, then by id
    query = select(User).where(User.clerk_user_id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # If not found by clerk_user_id, try by id (for testing)
        try:
            db_user_id = UUID(user_id)
            query = select(User).where(User.id == db_user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
        except ValueError:
            pass
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.get("/rate-limit", response_model=RateLimitResponse)
async def get_rate_limit(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Check remaining prompts and reset time"""
    # TODO: Convert user_id (Clerk ID) to database user_id
    if user_id == "placeholder_user_id":
        # Return default values for placeholder
        return RateLimitResponse(
            remaining_prompts=settings.MAX_PROMPTS_PER_HOUR,
            reset_time=datetime.utcnow() + timedelta(hours=1),
            max_prompts=settings.MAX_PROMPTS_PER_HOUR
        )
    
    # Find user
    query = select(User).where(User.clerk_user_id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # Try by id
        try:
            db_user_id = UUID(user_id)
            query = select(User).where(User.id == db_user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
        except ValueError:
            pass
    
    if not user:
        # User doesn't exist yet, return max prompts
        return RateLimitResponse(
            remaining_prompts=settings.MAX_PROMPTS_PER_HOUR,
            reset_time=datetime.utcnow() + timedelta(hours=1),
            max_prompts=settings.MAX_PROMPTS_PER_HOUR
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