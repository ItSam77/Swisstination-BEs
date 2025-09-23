from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List
import sys
import os

# Add the parent directory to the path to import supabase_client and auth
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from supabase_client import supabase
from app.routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

# Pydantic models
class PreferenceItem(BaseModel):
    kategori_id: int
    weight: float = 1.0

class SavePreferencesRequest(BaseModel):
    preferences: List[PreferenceItem]

class PreferencesResponse(BaseModel):
    message: str
    saved_count: int

# Add after line 24 (after saved_count: int)
class PreferenceStatusResponse(BaseModel):
    has_preferences: bool
    preference_count: int
    message: str

@router.get("/preferences/status", response_model=PreferenceStatusResponse)
async def check_user_preferences_status(current_user: dict = Depends(get_current_user)):
    """
    Check if user has set preferences (for redirect logic)
    """
    try:
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured."
            )
        
        user_id = current_user['user_id']
        
        # Check if user has any preferences in the test table
        result = supabase.table("preference").select("user_id").eq("user_id", user_id).execute()
        
        preference_count = len(result.data) if result.data else 0
        has_preferences = preference_count > 0
        
        return PreferenceStatusResponse(
            has_preferences=has_preferences,
            preference_count=preference_count,
            message=f"User {'has' if has_preferences else 'does not have'} preferences set"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Check preferences status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check preferences status: {str(e)}"
        )

@router.get("/")
async def get_users():
    return {"message": "Users endpoint - to be implemented"}

@router.post("/preferences", response_model=PreferencesResponse)
async def save_user_preferences(
    request: SavePreferencesRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Save user preferences to test table
    """
    try:
        print(f"Saving preferences for user: {current_user['user_id']}")  # Debug log
        
        # Check if Supabase is configured
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured. Please set up Supabase credentials."
            )
        
        user_id = current_user['user_id']
        
        # First, delete existing preferences for this user to replace them
        delete_result = supabase.table("preference").delete().eq("user_id", user_id).execute()
        print(f"Deleted existing preferences: {delete_result}")  # Debug log
        
        # Prepare data for insertion
        preferences_data = []
        for pref in request.preferences:
            preferences_data.append({
                "user_id": user_id,
                "kategori_id": pref.kategori_id,
                "weight": pref.weight
            })
        
        # Insert new preferences
        if preferences_data:
            insert_result = supabase.table("preference").insert(preferences_data).execute()
            print(f"Insert result: {insert_result}")  # Debug log
            
            if insert_result.data:
                return PreferencesResponse(
                    message="Preferences saved successfully!",
                    saved_count=len(preferences_data)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to save preferences"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No preferences provided"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Save preferences error: {str(e)}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save preferences: {str(e)}"
        )

@router.get("/preferences")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """
    Get user preferences from test table
    """
    try:
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured."
            )
        
        user_id = current_user['user_id']
        
        # Get user preferences with category details
        result = supabase.table("preference").select(
            "kategori_id, weight, category(label)"
        ).eq("user_id", user_id).execute()
        
        return {
            "message": "Preferences retrieved successfully",
            "preferences": result.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get preferences error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )
