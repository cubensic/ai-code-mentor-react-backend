from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class ProjectCreate(BaseModel):
    name: str
    template_type: str

class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    template_type: str
    created_at: datetime
    updated_at: datetime
    last_accessed: datetime
    file_count: int = 0

class Config:
    from_attributes = True # This allows Pydantic to convert SQLAlchemy models to Pydantic models
