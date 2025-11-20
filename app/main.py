from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import projects, files, chat, users

app = FastAPI(title="AI Code Learning Platform")

# DEBUG: Print allowed origins to logs
print(f"Allowed Origins: {settings.allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include project routes
app.include_router(projects.router)
app.include_router(files.router)
app.include_router(chat.router)
app.include_router(users.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "API is running!"}