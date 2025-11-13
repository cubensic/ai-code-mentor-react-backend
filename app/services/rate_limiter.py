from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.config import settings
from uuid import UUID

async def check_rate_limit(
    db: AsyncSession,
    user_id: UUID
) -> tuple[bool, int]:
    """
    Check if user can make a request (rate limit check).
    Returns: (can_proceed: bool, remaining_prompts: int)
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # User doesn't exist yet, create one (will be handled by auth later)
        return False, 0
    
    # Reset if hour has passed
    now = datetime.utcnow()
    if user.last_prompt_reset:
        time_diff = now - user.last_prompt_reset
        if time_diff > timedelta(hours=1):
            user.hourly_prompt_count = 0
            user.last_prompt_reset = now
            await db.commit()
    else:
        user.last_prompt_reset = now
        await db.commit()
    
    # Check limit
    max_prompts = settings.MAX_PROMPTS_PER_HOUR
    if user.hourly_prompt_count >= max_prompts:
        remaining = 0
        return False, remaining
    
    # Increment count
    user.hourly_prompt_count += 1
    await db.commit()
    
    remaining = max_prompts - user.hourly_prompt_count
    return True, remaining