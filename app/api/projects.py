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

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    sort_by: Optional[str] = "last_accessed",
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Get all projects for authenticated user"""
    # TODO: Convert user_id (Clerk ID) to database user_id
    # For now, using placeholder
    query = select(Project).where(Project.user_id == UUID(user_id) if user_id != "placeholder_user_id" else Project.user_id.isnot(None))
    
    if sort_by == "created_at":
        query = query.order_by(Project.created_at.desc())
    else:
        query = query.order_by(Project.last_accessed.desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    return projects


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Create new project"""
    # TODO: Convert user_id (Clerk ID) to database user_id
    db_user_id = UUID(user_id) if user_id != "placeholder_user_id" else UUID("00000000-0000-0000-0000-000000000000")
    
    # Check max projects limit
    can_create = await check_max_projects(db, db_user_id, max_projects=10)
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
        user_id=db_user_id,
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
    user_id: str = Depends(verify_clerk_token)
):
    """Get project details with all files"""
    query = select(Project).options(selectinload(Project.files)).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # TODO: Verify project belongs to user
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    name: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Rename project"""
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # TODO: Verify project belongs to user
    
    project.name = name
    await db.commit()
    await db.refresh(project)
    
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(verify_clerk_token)
):
    """Delete project and all associated files"""
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # TODO: Verify project belongs to user
    
    await db.delete(project)
    await db.commit()
    
    return None