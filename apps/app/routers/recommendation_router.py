from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add the parent directory to the path to import supabase_client and recommendation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from supabase_client import supabase
from recommendation import recommend
from app.routers.auth import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Pydantic models
class RecommendationItem(BaseModel):
    destinasi_id: str
    score: float

class RecommendationsResponse(BaseModel):
    message: str
    user_id: str
    recommendation_type: str  # "cold_start", "personalized", or "fallback"
    recommendations: List[RecommendationItem]
    based_on_categories: Optional[List[int]] = None

@router.get("/", response_model=RecommendationsResponse)
async def get_recommendations(
    n: int = Query(default=None, ge=1, description="Number of recommendations to return (default: all available)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get personalized recommendations based on user preferences.
    
    For new users (cold start): Uses category preferences to generate recommendations
    For existing users: Uses collaborative filtering based on past interactions
    """
    try:
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured."
            )
        
        user_id = current_user['user_id']
        print(f"Getting recommendations for user: {user_id}")  # Debug log
        
        # Fetch user preferences to extract kategori_ids
        preferences_result = supabase.table("preference").select(
            "kategori_id, weight"
        ).eq("user_id", user_id).execute()
        
        # Extract category IDs from preferences
        selected_cat_ids = None
        if preferences_result.data:
            selected_cat_ids = [pref["kategori_id"] for pref in preferences_result.data]
            print(f"User preferences (categories): {selected_cat_ids}")  # Debug log
        
        # Get recommendations using the recommendation engine
        # If n is None, get all available destinations (set to a large number)
        recommendation_count = n if n is not None else 1000  # Large number to get all destinations
        print(f"[DEBUG] Calling recommend with n={recommendation_count}")  # Debug log
        recommendations = recommend(
            user_id=user_id,
            selected_cat_ids=selected_cat_ids,
            n=recommendation_count
        )
        print(f"[DEBUG] Got {len(recommendations)} recommendations from recommend()")  # Debug log
        
        # Determine recommendation type
        if not recommendations:
            recommendation_type = "fallback"
            message = "No specific recommendations available. Showing popular items."
        elif selected_cat_ids and len(selected_cat_ids) > 0:
            # Check if this is likely a cold start user
            # (You might want to check actual interaction count here)
            recommendation_type = "cold_start"
            message = f"Cold start recommendations based on your category preferences"
        else:
            recommendation_type = "personalized"
            message = "Personalized recommendations based on your interaction history"
        
        # Format recommendations
        formatted_recommendations = [
            RecommendationItem(destinasi_id=str(item[0]), score=float(item[1]))
            for item in recommendations
        ]
        
        return RecommendationsResponse(
            message=message,
            user_id=user_id,
            recommendation_type=recommendation_type,
            recommendations=formatted_recommendations,
            based_on_categories=selected_cat_ids
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get recommendations error: {str(e)}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )

@router.get("/categories/{category_id}")
async def get_recommendations_by_category(
    category_id: int,
    n: int = Query(default=None, ge=1, description="Number of recommendations to return (default: all available)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get recommendations for a specific category.
    Useful for exploring recommendations in a particular category.
    """
    try:
        user_id = current_user['user_id']
        print(f"Getting recommendations for user: {user_id}, category: {category_id}")
        
        # Get recommendations for specific category
        # If n is None, get all available destinations (set to a large number)
        recommendation_count = n if n is not None else 1000  # Large number to get all destinations
        recommendations = recommend(
            user_id=user_id,
            selected_cat_ids=[category_id],
            n=recommendation_count
        )
        
        # Format recommendations
        formatted_recommendations = [
            RecommendationItem(destinasi_id=str(item[0]), score=float(item[1]))
            for item in recommendations
        ]
        
        return RecommendationsResponse(
            message=f"Recommendations for category {category_id}",
            user_id=user_id,
            recommendation_type="category_filtered",
            recommendations=formatted_recommendations,
            based_on_categories=[category_id]
        )
        
    except Exception as e:
        print(f"Get category recommendations error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category recommendations: {str(e)}"
        )

@router.post("/cold-start")
async def get_cold_start_recommendations(
    category_ids: List[int],
    n: int = Query(default=None, ge=1, description="Number of recommendations to return (default: all available)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get cold start recommendations for specific categories.
    Useful for testing or getting recommendations without saving preferences.
    """
    try:
        user_id = current_user['user_id']
        print(f"Getting cold start recommendations for categories: {category_ids}")
        
        # Force cold start by setting user_id to None
        # If n is None, get all available destinations (set to a large number)
        recommendation_count = n if n is not None else 1000  # Large number to get all destinations
        recommendations = recommend(
            user_id=None,  # Force cold start
            selected_cat_ids=category_ids,
            n=recommendation_count
        )
        
        # Format recommendations
        formatted_recommendations = [
            RecommendationItem(destinasi_id=str(item[0]), score=float(item[1]))
            for item in recommendations
        ]
        
        return RecommendationsResponse(
            message=f"Cold start recommendations for categories: {category_ids}",
            user_id=user_id,
            recommendation_type="cold_start",
            recommendations=formatted_recommendations,
            based_on_categories=category_ids
        )
        
    except Exception as e:
        print(f"Get cold start recommendations error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cold start recommendations: {str(e)}"
        )
