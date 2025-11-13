from fastapi import HTTPException, Depends, Header
from typing import Optional

# Placeholder - will be replaced with Clerk JWT verification later
async def verify_clerk_token(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> str:
    """
    Placeholder auth dependency.
    TODO: Replace with actual Clerk JWT verification
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    
    # Extract token from "Bearer <token>" format
    if authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    else:
        token = authorization
    
    # For now, return a placeholder user_id
    # Later: decode JWT and extract user_id from Clerk token
    return "placeholder_user_id"