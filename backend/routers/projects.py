from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
import logging
import json
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
from services.seo_keywords_service import SEOKeywordsService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

def parse_serp_api_contents(project: dict) -> dict:
    """
    Parse serp_api_contents from JSON string to dictionary if needed
    """
    if project.get('serp_api_contents') and isinstance(project['serp_api_contents'], str):
        try:
            project['serp_api_contents'] = json.loads(project['serp_api_contents'])
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse serp_api_contents as JSON for project {project.get('id', 'unknown')}: {e}")
            project['serp_api_contents'] = None
    return project

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
        
        # Prepare project data with all required fields
        project_data = {
            "user_id": user_id,
            "name": project.name,
            "description": project.description,
            "num_blogs": project.num_blogs,
            "completed_blogs": 0,  # Initialize with 0 completed blogs
            "status": "ready",  # Set status to "ready" instead of "pending"
            "wordpress_account_id": str(project.wordpress_account_id) if project.wordpress_account_id else None,
            "api_keys": project.api_keys,
            "settings": None,  # Initialize as None
            "draft_creation_model": project.draft_creation_model,  # Use draft_creation_model from request
            "content_vetting_model": project.draft_creation_model,  # Use draft_creation_model from request
            "model_settings": None,  # Initialize as None
            "workflow_preferences": None,  # Initialize as None
            "serp_api_on": project.serp_api_on,  # Store SerpAPI setting
            "enhanced_research": project.enhanced_research,  # Store enhanced research setting
            "serp_api_contents": None,  # Initialize as None (will be populated during research)
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
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
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
        
        # Parse serp_api_contents for each project if it's a JSON string
        projects = [ProjectResponse(**parse_serp_api_contents(project)) for project in response.data]
        
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
        project = parse_serp_api_contents(project)
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
        
        updated_project = parse_serp_api_contents(updated_project)
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
            num_blogs=project["num_blogs"],
            created_at=project["created_at"],
            updated_at=project["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch project status: {str(e)}")

@router.post("/{project_id}/extract-seo-keywords", summary="Extract SEO keywords from SerpAPI research")
async def extract_seo_keywords(
    project_id: str,
    # Temporarily disable authentication for testing
    # current_user: dict = Depends(get_current_user)
):
    """
    Extract SEO keywords from serp_api_contents and store in extracted_seo_keywords column
    """
    try:
        logger.info(f"🔍 SEO keywords extraction endpoint called for project: {project_id}")
        
        # Temporarily skip user verification for testing
        # project_response = supabase_client.table("projects").select("user_id").eq("id", project_id).execute()
        # 
        # if not project_response.data:
        #     raise HTTPException(status_code=404, detail="Project not found")
        # 
        # project = project_response.data[0]
        # if project["user_id"] != current_user["id"]:
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        logger.info(f"🔍 Starting SEO keywords extraction for project: {project_id}")
        
        # Extract SEO keywords
        success = SEOKeywordsService.extract_seo_keywords(project_id)
        
        if success:
            logger.info(f"✅ SEO keywords extracted successfully for project: {project_id}")
            return {"message": "SEO keywords extracted and stored successfully"}
        else:
            logger.error(f"❌ SEO keywords extraction failed for project: {project_id}")
            raise HTTPException(status_code=500, detail="Failed to extract SEO keywords")
            
    except HTTPException:
        logger.error(f"❌ HTTPException in SEO keywords extraction for project: {project_id}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in SEO keywords extraction for project: {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract SEO keywords: {str(e)}")

@router.post("/{project_id}/check-status", summary="Check and update project status based on blog generation and publishing")
async def check_project_status(
    project_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Check and update project status based on blog generation and publishing progress
    """
    try:
        user_id = current_user["id"]
        
        # Verify project belongs to user
        project_response = supabase_client.table("projects").select("id, user_id").eq("id", str(project_id)).execute()
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = project_response.data[0]
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Import and call the status check function
        from tasks.wordpress_publishing import check_and_update_project_status
        check_and_update_project_status(str(project_id))
        
        # Get updated project status
        updated_response = supabase_client.table("projects").select("status, completed_blogs, num_blogs").eq("id", str(project_id)).execute()
        if updated_response.data:
            updated_project = updated_response.data[0]
            return {
                "message": "Project status checked and updated",
                "project_id": str(project_id),
                "status": updated_project["status"],
                "completed_blogs": updated_project["completed_blogs"],
                "num_blogs": updated_project["num_blogs"]
            }
        
        return {"message": "Project status checked and updated", "project_id": str(project_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking project status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check project status: {str(e)}")

@router.post("/check-all-statuses", summary="Check and update all project statuses for the current user")
async def check_all_project_statuses(
    current_user: dict = Depends(get_current_user)
):
    """
    Check and update all project statuses for the current user based on blog generation and publishing progress
    """
    try:
        user_id = current_user["id"]
        
        # Get all projects for the user
        projects_response = supabase_client.table("projects").select("id, name, status, completed_blogs, num_blogs").eq("user_id", user_id).execute()
        if not projects_response.data:
            return {"message": "No projects found for user", "projects_updated": 0}
        
        projects = projects_response.data
        updated_count = 0
        
        # Import and call the status check function for each project
        from tasks.wordpress_publishing import check_and_update_project_status
        
        for project in projects:
            try:
                check_and_update_project_status(str(project["id"]))
                updated_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Could not update status for project {project['id']}: {e}")
                continue
        
        logger.info(f"✅ Updated statuses for {updated_count}/{len(projects)} projects for user {user_id}")
        
        return {
            "message": f"Project statuses checked and updated for {updated_count} projects",
            "projects_updated": updated_count,
            "total_projects": len(projects)
        }
        
    except Exception as e:
        logger.error(f"Error checking all project statuses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check project statuses: {str(e)}")
