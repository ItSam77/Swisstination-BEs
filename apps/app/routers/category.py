from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
import sys
import os

# Add the parent directory to the path to import supabase_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from supabase_client import supabase

router = APIRouter(prefix="/categories", tags=["Categories"])

# Pydantic models for response
class Category(BaseModel):
    kategori_id: int
    nama: str
    label: str

class CategoriesResponse(BaseModel):
    categories: List[Category]

@router.get("/", response_model=List[Category])
async def get_categories():
    """
    Get all categories from the category table
    Returns only kategori_id, nama, and label fields
    """
    try:
        # Check if Supabase is configured
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured. Please set up Supabase credentials."
            )
        
        # Fetch all categories from the category table
        result = supabase.table("category").select("kategori_id, nama, label").execute()
        
        if result.data:
            return result.data
        else:
            # Return empty list if no categories found
            return []
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Categories fetch error: {str(e)}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch categories: {str(e)}"
        )

@router.get("/test")
async def test_categories():
    """
    Test endpoint to verify category table connectivity
    """
    try:
        if supabase is None:
            return {"message": "Database connection not configured"}
        
        # Test connection by counting categories
        result = supabase.table("category").select("kategori_id", count="exact").execute()
        return {
            "message": "Category endpoint is working!",
            "total_categories": result.count if result.count is not None else 0
        }
    except Exception as e:
        return {"message": f"Category test failed: {str(e)}"}