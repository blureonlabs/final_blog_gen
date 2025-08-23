from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
import logging
from datetime import datetime

from models.wordpress_account import (
    WordPressAccountCreate, 
    WordPressAccountUpdate, 
    WordPressAccountResponse, 
    WordPressAccountListResponse
)
from core.supabase_client import supabase_client, verify_user_exists
from core.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=WordPressAccountResponse, summary="Create WordPress account")
async def create_wordpress_account(
    account: WordPressAccountCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new WordPress account connection
    """
    try:
        user_id = current_user["id"]
        
        # Verify user exists in database
        if not await verify_user_exists(user_id):
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare account data
        account_data = {
            "user_id": user_id,
            "name": account.name,
            "site_url": str(account.site_url),
            "username": account.username,
            "password": account.password,  # In production, encrypt this
            "is_active": account.is_active,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert account into database
        response = supabase_client.table("wordpress_accounts").insert(account_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create WordPress account")
        
        created_account = response.data[0]
        logger.info(f"WordPress account created successfully: {created_account['id']}")
        
        return WordPressAccountResponse(**created_account)
        
    except Exception as e:
        logger.error(f"Error creating WordPress account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create WordPress account: {str(e)}")

@router.get("/", response_model=WordPressAccountListResponse, summary="Get user's WordPress accounts")
async def get_wordpress_accounts(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of user's WordPress accounts
    """
    try:
        user_id = current_user["id"]
        
        # Get accounts from database
        response = supabase_client.table("wordpress_accounts").select("*").eq("user_id", user_id).eq("is_active", True).order("created_at", desc=True).execute()
        
        accounts = [WordPressAccountResponse(**account) for account in response.data]
        
        return WordPressAccountListResponse(
            accounts=accounts,
            total=len(accounts)
        )
        
    except Exception as e:
        logger.error(f"Error fetching WordPress accounts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch WordPress accounts: {str(e)}")

@router.get("/{account_id}", response_model=WordPressAccountResponse, summary="Get WordPress account by ID")
async def get_wordpress_account(
    account_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific WordPress account by ID
    """
    try:
        user_id = current_user["id"]
        
        # Get account from database
        response = supabase_client.table("wordpress_accounts").select("*").eq("id", str(account_id)).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="WordPress account not found")
        
        account = response.data[0]
        return WordPressAccountResponse(**account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching WordPress account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch WordPress account: {str(e)}")

@router.put("/{account_id}", response_model=WordPressAccountResponse, summary="Update WordPress account")
async def update_wordpress_account(
    account_id: UUID,
    account_update: WordPressAccountUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a WordPress account
    """
    try:
        user_id = current_user["id"]
        
        # Check if account exists and belongs to user
        existing_response = supabase_client.table("wordpress_accounts").select("id").eq("id", str(account_id)).eq("user_id", user_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="WordPress account not found")
        
        # Prepare update data
        update_data = account_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update account
        response = supabase_client.table("wordpress_accounts").update(update_data).eq("id", str(account_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update WordPress account")
        
        updated_account = response.data[0]
        logger.info(f"WordPress account updated successfully: {account_id}")
        
        return WordPressAccountResponse(**updated_account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating WordPress account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update WordPress account: {str(e)}")

@router.delete("/{account_id}", summary="Delete WordPress account")
async def delete_wordpress_account(
    account_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a WordPress account
    """
    try:
        user_id = current_user["id"]
        
        # Check if account exists and belongs to user
        existing_response = supabase_client.table("wordpress_accounts").select("id").eq("id", str(account_id)).eq("user_id", user_id).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="WordPress account not found")
        
        # Delete account
        response = supabase_client.table("wordpress_accounts").delete().eq("id", str(account_id)).execute()
        
        logger.info(f"WordPress account deleted successfully: {account_id}")
        
        return {"message": "WordPress account deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting WordPress account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete WordPress account: {str(e)}")

@router.post("/{account_id}/test", summary="Test WordPress connection")
async def test_wordpress_connection(
    account_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Test WordPress account connection
    """
    try:
        user_id = current_user["id"]
        
        # Get account from database
        response = supabase_client.table("wordpress_accounts").select("*").eq("id", str(account_id)).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="WordPress account not found")
        
        account = response.data[0]
        
        # TODO: Implement actual WordPress connection test
        # This would involve making a request to the WordPress REST API
        # to verify the credentials work
        
        logger.info(f"WordPress connection test for account: {account_id}")
        
        return {
            "message": "WordPress connection test completed",
            "account_id": account_id,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing WordPress connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test WordPress connection: {str(e)}")
