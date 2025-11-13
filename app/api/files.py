from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.database import get_db
from app.api.auth import verify_clerk_token
from app.models.file import File
from app.models.project import Project
from app.schemas.file import FileCreate, FileUpdate, FileResponse

router = APIRouter(prefix="/api", tags=["files"])

# Valid file types
VALID_FILE_TYPES = ["html", "css", "js", "txt"]

@router.post("/projects/{project_id}/files", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(
    project_id: UUID,
    file_data: FileCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Create new file in project"""
    # Validate file type
    if file_data.file_type not in VALID_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Must be one of: {VALID_FILE_TYPES}"
        )
    
    # Verify project exists
    project_query = select(Project).where(Project.id == project_id)
    project_result = await db.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # TODO: Verify project belongs to user
    
    # Check if file with same name already exists
    existing_file_query = select(File).where(
        File.project_id == project_id,
        File.name == file_data.name
    )
    existing_file_result = await db.execute(existing_file_query)
    existing_file = existing_file_result.scalar_one_or_none()
    
    if existing_file:
        raise HTTPException(
            status_code=400,
            detail=f"File with name '{file_data.name}' already exists in this project"
        )
    
    # Create file
    file = File(
        project_id=project_id,
        name=file_data.name,
        file_type=file_data.file_type,
        content=file_data.content or ""
    )
    
    db.add(file)
    await db.commit()
    await db.refresh(file)
    
    return file

@router.get("/projects/{project_id}/files", response_model=List[FileResponse])
async def get_files(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Get all files for project"""
    # Verify project exists
    project_query = select(Project).where(Project.id == project_id)
    project_result = await db.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # TODO: Verify project belongs to user
    
    # Get all files
    files_query = select(File).where(File.project_id == project_id)
    files_result = await db.execute(files_query)
    files = files_result.scalars().all()
    
    return files

@router.put("/files/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: UUID,
    file_data: FileUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Update file content (autosave)"""
    file_query = select(File).where(File.id == file_id)
    file_result = await db.execute(file_query)
    file = file_result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # TODO: Verify file belongs to user's project
    
    # Update content
    if file_data.content is not None:
        file.content = file_data.content
    
    await db.commit()
    await db.refresh(file)
    
    return file

@router.put("/files/{file_id}/rename", response_model=FileResponse)
async def rename_file(
    file_id: UUID,
    name: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Rename file"""
    file_query = select(File).where(File.id == file_id)
    file_result = await db.execute(file_query)
    file = file_result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # TODO: Verify file belongs to user's project
    
    # Check if another file with same name exists
    existing_file_query = select(File).where(
        File.project_id == file.project_id,
        File.name == name,
        File.id != file_id
    )
    existing_file_result = await db.execute(existing_file_query)
    existing_file = existing_file_result.scalar_one_or_none()
    
    if existing_file:
        raise HTTPException(
            status_code=400,
            detail=f"File with name '{name}' already exists in this project"
        )
    
    file.name = name
    await db.commit()
    await db.refresh(file)
    
    return file

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Delete file"""
    file_query = select(File).where(File.id == file_id)
    file_result = await db.execute(file_query)
    file = file_result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # TODO: Verify file belongs to user's project
    
    await db.delete(file)
    await db.commit()
    
    return None