from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class UserResponse(BaseModel):
    id: UUID
    clerk_user_id: str
    email: str
    username: Optional[str]
    created_at: datetime
    updated_at: datetime
    project_count: int
    hourly_prompt_count: int
    last_prompt_reset: datetime
    
    class Config:
        from_attributes = True

class RateLimitResponse(BaseModel):
    remaining_prompts: int
    reset_time: datetime
    max_prompts: int