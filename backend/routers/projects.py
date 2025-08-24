from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
import logging
from datetime import datetime

from models.project import (
    ProjectCreate, 
    ProjectUpdate, 
    ProjectResponse, 
    ProjectListResponse,
    ProjectStatus
)
from core.supabase_client import supabase_client, verify_user_exists
from core.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create", response_model=ProjectResponse, summary="Create a new project")
async def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new blog generation project
    """
    try:
        user_id = current_user["id"]
        
        # Verify user exists in database
        if not await verify_user_exists(user_id):
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare project data
        project_data = {
            "user_id": user_id,
            "name": project.name,
            "description": project.description,
            "num_blogs": project.num_blogs,
            "ai_model": project.ai_model,
            "wordpress_account_id": str(project.wordpress_account_id) if project.wordpress_account_id else None,
            "api_keys": project.api_keys,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert project into database
        response = supabase_client.table("projects").insert(project_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create project")
        
        created_project = response.data[0]
        logger.info(f"Project created successfully: {created_project['id']}")
        
        return ProjectResponse(**created_project)
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@router.get("/", response_model=ProjectListResponse, summary="Get user's projects")
async def get_projects(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated list of user's projects
    """
    try:
        user_id = current_user["id"]
        
        # Build query
        query = supabase_client.table("projects").select("*").eq("user_id", user_id)
        
        # Add status filter if provided
        if status:
            query = query.eq("status", status)
        
        # Get total count
        count_response = query.execute()
        total = len(count_response.data)
        
        # Get paginated results
        offset = (page - 1) * per_page
        response = query.range(offset, offset + per_page - 1).order("created_at", desc=True).execute()
        
        projects = [ProjectResponse(**project) for project in response.data]
        
        return ProjectListResponse(
            projects=projects,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project by ID")
async def get_project(
    project_id: UUID,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Get a specific project by ID
    """
    try:
        # Temporarily use a mock user ID for testing
        # user_id = current_user["id"]
        
        # Get project from database
        response = supabase_client.table("projects").select("*").eq("id", str(project_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = response.data[0]
        return ProjectResponse(**project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch project: {str(e)}")

@router.put("/{project_id}", response_model=ProjectResponse, summary="Update project")
async def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a project
    """
    try:
        user_id = current_user["id"]
        
        # Check if project exists and belongs to user
        existing_response = supabase_client.table("projects").select("id").eq("id", str(project_id)).eq("user_id", user_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Prepare update data
        update_data = project_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update project
        response = supabase_client.table("projects").update(update_data).eq("id", str(project_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update project")
        
        updated_project = response.data[0]
        logger.info(f"Project updated successfully: {project_id}")
        
        return ProjectResponse(**updated_project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@router.delete("/{project_id}", summary="Delete project")
async def delete_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a project
    """
    try:
        user_id = current_user["id"]
        
        # Check if project exists and belongs to user
        existing_response = supabase_client.table("projects").select("id").eq("id", str(project_id)).eq("user_id", user_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete project
        response = supabase_client.table("projects").delete().eq("id", str(project_id)).execute()
        
        logger.info(f"Project deleted successfully: {project_id}")
        
        return {"message": "Project deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

@router.get("/{project_id}/status", response_model=ProjectStatus, summary="Get project status")
async def get_project_status(
    project_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get project status and progress
    """
    try:
        user_id = current_user["id"]
        
        # Get project from database
        response = supabase_client.table("projects").select("*").eq("id", str(project_id)).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = response.data[0]
        
        # Calculate progress (placeholder - will be updated when blogs are generated)
        progress = 0
        blogs_generated = 0
        
        # TODO: Get actual blog count from blogs table
        # blogs_response = supabase_client.table("blogs").select("count").eq("project_id", str(project_id)).execute()
        # blogs_generated = blogs_response.data[0]["count"] if blogs_response.data else 0
        # progress = int((blogs_generated / project["num_blogs"]) * 100)
        
        return ProjectStatus(
            id=project["id"],
            name=project["name"],
            status=project["status"],
            progress=progress,
            blogs_generated=blogs_generated,
            total_blogs=project["num_blogs"],
            created_at=project["created_at"],
            updated_at=project["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch project status: {str(e)}")
