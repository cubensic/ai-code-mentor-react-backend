from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.api.auth import verify_clerk_token
from app.models.project import Project
from app.models.file import File
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import create_initial_files, check_max_projects
from app.services.user_service import get_or_create_user

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    sort_by: Optional[str] = "last_accessed",
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Get all projects for authenticated user"""
    # Get or create database user from Clerk ID
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",  # Temporary - will get from token later
        username=None
    )
    
    # Query projects for this user
    query = select(
        Project,
        func.count(File.id).label('file_count')
    ).outerjoin(
        File, Project.id == File.project_id
    ).where(
        Project.user_id == user.id
    ).group_by(Project.id)
    
    if sort_by == "created_at":
        query = query.order_by(Project.created_at.desc())
    else:
        query = query.order_by(Project.last_accessed.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    # Convert to ProjectResponse with file_count
    projects = []
    for project, file_count in rows:
        project_dict = {
            "id": project.id,
            "user_id": project.user_id,
            "name": project.name,
            "template_type": project.template_type,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "last_accessed": project.last_accessed,
            "file_count": file_count or 0
        }
        projects.append(project_dict)
    
    return projects


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Create new project"""
    # Get or create database user
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",
        username=None
    )
    
    # Check max projects limit
    can_create = await check_max_projects(db, user.id, max_projects=10)
    if not can_create:
        raise HTTPException(
            status_code=400,
            detail="Maximum number of projects (10) reached"
        )
    
    # Validate template type
    if project_data.template_type not in ["portfolio_website", "todo_app", "calculator"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template type: {project_data.template_type}"
        )
    
    # Create project
    project = Project(
        user_id=user.id,  # Use database user ID
        name=project_data.name,
        template_type=project_data.template_type
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    # Create initial files based on template
    await create_initial_files(db, project.id, project_data.template_type)
    
    return project

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Get project details with all files"""
    # Get or create database user
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",
        username=None
    )
    
    query = select(Project).options(selectinload(Project.files)).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify project belongs to user
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    name: str,
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Rename project"""
    # Get or create database user
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",
        username=None
    )
    
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify project belongs to user
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    project.name = name
    await db.commit()
    await db.refresh(project)
    
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    clerk_user_id: str = Depends(verify_clerk_token)
):
    """Delete project and all associated files"""
    # Get or create database user
    user = await get_or_create_user(
        db=db,
        clerk_user_id=clerk_user_id,
        email=f"{clerk_user_id}@placeholder.com",
        username=None
    )
    
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify project belongs to user
    if project.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.delete(project)
    await db.commit()
    
    return None