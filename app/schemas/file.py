from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class FileCreate(BaseModel):
    name: str
    file_type: str
    content: Optional[str] = None

class FileUpdate(BaseModel):
    content: Optional[str] = None

class FileResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    file_type: str
    content: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True