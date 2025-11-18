from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
import uuid

async def get_or_create_user(
    db: AsyncSession,
    clerk_user_id: str,
    email: str = None,
    username: str = None
) -> User:
    """
    Get existing user or create new one from Clerk authentication.
    Returns the User model instance.
    """
    # Try to find existing user by Clerk ID
    query = select(User).where(User.clerk_user_id == clerk_user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user:
        # Update email/username if provided and different
        if email and user.email != email:
            user.email = email
        if username and user.username != username:
            user.username = username
        if email or username:
            await db.commit()
            await db.refresh(user)
        return user
    
    # Create new user - email is required
    if not email:
        raise ValueError("Email is required to create a new user")
    
    new_user = User(
        id=uuid.uuid4(),
        clerk_user_id=clerk_user_id,
        email=email,
        username=username
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_clerk_id(
    db: AsyncSession,
    clerk_user_id: str
) -> User | None:
    """Get user by Clerk user ID, returns None if not found"""
    query = select(User).where(User.clerk_user_id == clerk_user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()