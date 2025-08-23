from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
import logging
from datetime import datetime

from models.api_key import (
    APIKeyCreate, 
    APIKeyUpdate, 
    APIKeyResponse, 
    APIKeyListResponse,
    ServiceAPIKeys
)
from core.supabase_client import supabase_client, verify_user_exists
from core.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=APIKeyResponse, summary="Create API key")
async def create_api_key(
    api_key: APIKeyCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new API key for external services
    """
    try:
        user_id = current_user["id"]
        
        # Verify user exists in database
        if not await verify_user_exists(user_id):
            raise HTTPException(status_code=404, detail="User not found")
        
        # If this is set as default, unset other defaults for the same service
        if api_key.is_default:
            await _unset_default_for_service(user_id, api_key.service)
        
        # Prepare key data
        key_data = {
            "user_id": user_id,
            "name": api_key.name,
            "service": api_key.service.lower(),  # Normalize service name
            "api_key": api_key.api_key,  # In production, encrypt this
            "is_default": api_key.is_default,
            "is_active": api_key.is_active,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert key into database
        response = supabase_client.table("api_keys").insert(key_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create API key")
        
        created_key = response.data[0]
        logger.info(f"API key created successfully: {created_key['id']}")
        
        return APIKeyResponse(**created_key)
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")

@router.get("/", response_model=APIKeyListResponse, summary="Get user's API keys")
async def get_api_keys(
    service: Optional[str] = Query(None, description="Filter by service"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of user's API keys
    """
    try:
        user_id = current_user["id"]
        
        # Build query
        query = supabase_client.table("api_keys").select("*").eq("user_id", user_id).eq("is_active", True)
        
        # Add service filter if provided
        if service:
            query = query.eq("service", service.lower())
        
        # Get keys from database
        response = query.order("created_at", desc=True).execute()
        
        api_keys = [APIKeyResponse(**key) for key in response.data]
        
        return APIKeyListResponse(
            api_keys=api_keys,
            total=len(api_keys)
        )
        
    except Exception as e:
        logger.error(f"Error fetching API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch API keys: {str(e)}")

@router.get("/services", response_model=ServiceAPIKeys, summary="Get API keys grouped by service")
async def get_service_api_keys(
    current_user: dict = Depends(get_current_user)
):
    """
    Get API keys grouped by service (OpenAI, Gemini, SERP)
    """
    try:
        user_id = current_user["id"]
        
        # Get all active API keys for the user
        response = supabase_client.table("api_keys").select("*").eq("user_id", user_id).eq("is_active", True).execute()
        
        # Group by service
        service_keys = {}
        for key in response.data:
            service = key["service"].lower()
            if service not in service_keys:
                service_keys[service] = []
            service_keys[service].append(APIKeyResponse(**key))
        
        # Get default keys for each service
        openai_key = next((k for k in service_keys.get("openai", []) if k.is_default), None)
        gemini_key = next((k for k in service_keys.get("gemini", []) if k.is_default), None)
        serp_key = next((k for k in service_keys.get("serp", []) if k.is_default), None)
        
        return ServiceAPIKeys(
            openai=openai_key,
            gemini=gemini_key,
            serp=serp_key
        )
        
    except Exception as e:
        logger.error(f"Error fetching service API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch service API keys: {str(e)}")

@router.get("/{key_id}", response_model=APIKeyResponse, summary="Get API key by ID")
async def get_api_key(
    key_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific API key by ID
    """
    try:
        user_id = current_user["id"]
        
        # Get key from database
        response = supabase_client.table("api_keys").select("*").eq("id", str(key_id)).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="API key not found")
        
        key = response.data[0]
        return APIKeyResponse(**key)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch API key: {str(e)}")

@router.put("/{key_id}", response_model=APIKeyResponse, summary="Update API key")
async def update_api_key(
    key_id: UUID,
    key_update: APIKeyUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an API key
    """
    try:
        user_id = current_user["id"]
        
        # Check if key exists and belongs to user
        existing_response = supabase_client.table("api_keys").select("id").eq("id", str(key_id)).eq("user_id", user_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # If this is set as default, unset other defaults for the same service
        if key_update.is_default:
            await _unset_default_for_service(user_id, key_update.service)
        
        # Prepare update data
        update_data = key_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update key
        response = supabase_client.table("api_keys").update(update_data).eq("id", str(key_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update API key")
        
        updated_key = response.data[0]
        logger.info(f"API key updated successfully: {key_id}")
        
        return APIKeyResponse(**updated_key)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update API key: {str(e)}")

@router.delete("/{key_id}", summary="Delete API key")
async def delete_api_key(
    key_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an API key
    """
    try:
        user_id = current_user["id"]
        
        # Check if key exists and belongs to user
        existing_response = supabase_client.table("api_keys").select("id").eq("id", str(key_id)).eq("user_id", user_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Delete key
        response = supabase_client.table("api_keys").delete().eq("id", str(key_id)).execute()
        
        logger.info(f"API key deleted successfully: {key_id}")
        
        return {"message": "API key deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete API key: {str(e)}")

async def _unset_default_for_service(user_id: str, service: str):
    """
    Helper function to unset default flag for other keys of the same service
    """
    try:
        # Update all other keys of the same service to not be default
        supabase_client.table("api_keys").update({"is_default": False}).eq("user_id", user_id).eq("service", service.lower()).eq("is_default", True).execute()
    except Exception as e:
        logger.warning(f"Failed to unset default for service {service}: {e}")
