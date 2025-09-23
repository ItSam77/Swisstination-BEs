from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path to import supabase_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from supabase_client import supabase
from .auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["reviews"])

class SubmitReviewRequest(BaseModel):
    destination_id: int
    rating: int  # 1-5 stars
    review: Optional[str] = None  # Optional review text

class ReviewResponse(BaseModel):
    message: str
    review_id: Optional[int] = None

@router.post("/", response_model=ReviewResponse)
async def submit_review(
    request: SubmitReviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a review and rating for a destination.
    Rating is required (1-5 stars), review text is optional.
    """
    try:
        # Validate rating range
        if request.rating < 1 or request.rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1 and 5 stars"
            )
        
        # Check if Supabase is configured
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured"
            )
        
        user_id = current_user['user_id']
        
        # Check if destination exists
        dest_check = supabase.table("destinasi").select("destinasi_id").eq("destinasi_id", request.destination_id).execute()
        if not dest_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Destination with ID {request.destination_id} not found"
            )
        
        # Check if user already reviewed this destination
        existing_review = supabase.table("ratings").select("*").eq("user_id", user_id).eq("destinasi_id", request.destination_id).execute()
        
        if existing_review.data:
            # Update existing review
            update_data = {
                "rating": request.rating,
                "review": request.review
            }
            
            result = supabase.table("ratings").update(update_data).eq("user_id", user_id).eq("destinasi_id", request.destination_id).execute()
            
            if result.data:
                return ReviewResponse(
                    message=f"Review updated successfully for destination {request.destination_id}!",
                    review_id=result.data[0].get('id') if result.data[0] else None
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to update review"
                )
        else:
            # Insert new review
            insert_data = {
                "user_id": user_id,
                "destinasi_id": request.destination_id,
                "rating": request.rating,
                "review": request.review
            }
            
            result = supabase.table("ratings").insert(insert_data).execute()
            
            if result.data:
                return ReviewResponse(
                    message=f"Review submitted successfully for destination {request.destination_id}!",
                    review_id=result.data[0].get('id') if result.data[0] else None
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to submit review"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"Submit review error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit review: {str(e)}"
        )

@router.get("/user")
async def get_user_reviews(current_user: dict = Depends(get_current_user)):
    """
    Get all reviews submitted by the current user.
    """
    try:
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured"
            )
        
        user_id = current_user['user_id']
        
        # Get user's reviews with destination info
        result = supabase.table("ratings").select(
            "*, destinasi:destinasi_id(nama_destinasi, kategori_id)"
        ).eq("user_id", user_id).execute()
        
        return {
            "reviews": result.data or [],
            "total": len(result.data) if result.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user reviews error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reviews: {str(e)}"
        )

