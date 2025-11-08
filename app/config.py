from pydantic_settings import BaseSettings
from pathlib import Path

# Get the directory where this config.py file is located
BASE_DIR = Path(__file__).parent.parent  # Goes up from app/ to backend/

class Settings(BaseSettings):
    # Database (optional for now)
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/aicode_db"
    
    # Clerk (optional for now)
    CLERK_JWT_KEY: str = "placeholder_key"
    
    # OpenAI (optional for now)
    OPENAI_API_KEY: str = "placeholder_key"
    
    # Rate Limiting
    MAX_PROMPTS_PER_HOUR: int = 20
    MAX_PROJECTS_PER_USER: int = 10
    
    # CORS (required!)
    FRONTEND_URL: str = "http://localhost:5173"
    
    class Config:
        env_file = BASE_DIR / ".env"  # Points to backend/.env

settings = Settings()