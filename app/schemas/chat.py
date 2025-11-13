from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import List, Optional

class ChatMessage(BaseModel):
    id: UUID
    project_id: UUID
    role: str  # 'user' or 'assistant'
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    project_id: UUID
    message: str
    files_context: Optional[List[dict]] = None