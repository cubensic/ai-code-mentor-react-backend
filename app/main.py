from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings  

app = FastAPI(title="AI Code Learning Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "API is running!"}