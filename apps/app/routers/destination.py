from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add the parent directory to the path to import supabase_client and auth
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from supabase_client import supabase
from app.routers.auth import get_current_user

router = APIRouter(prefix="/destinations", tags=["Destinations"])

# Pydantic models
class Destination(BaseModel):
    destinasi_id: str
    nama_destinasi: str
    kategori_id: int
    deskripsi: str
    image_url: Optional[str] = None

class DestinationDetails(BaseModel):
    destinasi_id: int  # Changed from str to int to match database
    nama_destinasi: str
    kategori_id: int
    deskripsi: str
    full_deskripsi: Optional[str] = None  # New detailed description field
    image_url: Optional[str] = None
    category_name: Optional[str] = None

class DestinationsResponse(BaseModel):
    destinations: List[Destination]

@router.get("/", response_model=DestinationsResponse)
async def get_all_destinations(current_user: dict = Depends(get_current_user)):
    """
    Get all destinations with basic information
    """
    try:
        print(f"Get all destinations request from user: {current_user.get('user_id', 'unknown')}")
        
        if supabase is None:
            print("ERROR: Supabase client is None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured."
            )
        
        # Fetch all destinations including image_url, ordered by destinasi_id
        print("Executing Supabase query...")
        result = supabase.table("destinasi").select(
            "destinasi_id, nama_destinasi, kategori_id, deskripsi, image_url"
        ).order("destinasi_id").execute()
        
        print(f"Query result: {len(result.data) if result.data else 0} destinations found")
        if result.data:
            # Convert data types to match Pydantic model
            destinations = []
            for dest in result.data:
                destinations.append({
                    "destinasi_id": str(dest["destinasi_id"]),  # Convert to string
                    "nama_destinasi": dest["nama_destinasi"],
                    "kategori_id": int(dest["kategori_id"]),
                    "deskripsi": dest["deskripsi"],
                    "image_url": dest.get("image_url")
                })
            return {"destinations": destinations}
        else:
            return {"destinations": []}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get destinations error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get destinations: {str(e)}"
        )

@router.get("/{destination_id}", response_model=DestinationDetails)
async def get_destination_by_id(
    destination_id: int, 
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific destination by ID with detailed information
    """
    try:
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured."
            )
        
        # Fetch destination with category name, image_url, and full_deskripsi
        result = supabase.table("destinasi").select(
            "destinasi_id, nama_destinasi, kategori_id, deskripsi, full_deskripsi, image_url, category(nama)"
        ).eq("destinasi_id", destination_id).execute()
        
        if result.data and len(result.data) > 0:
            destination = result.data[0]
            return {
                "destinasi_id": int(destination["destinasi_id"]),  # Ensure it's int
                "nama_destinasi": destination["nama_destinasi"],
                "kategori_id": int(destination["kategori_id"]),
                "deskripsi": destination["deskripsi"],
                "full_deskripsi": destination.get("full_deskripsi"),
                "image_url": destination.get("image_url"),
                "category_name": destination.get("category", {}).get("nama") if destination.get("category") else None
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Destination with ID {destination_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get destination by ID error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get destination: {str(e)}"
        )

@router.post("/batch", response_model=List[DestinationDetails])
async def get_destinations_by_ids(
    destination_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """
    Get multiple destinations by their IDs
    """
    try:
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured."
            )
        
        if not destination_ids:
            return []
        
        print(f"Fetching destinations for IDs: {destination_ids}")  # Debug log
        
        # Try to convert string IDs to integers if needed
        processed_ids = []
        for dest_id in destination_ids:
            try:
                # Try as integer first
                processed_ids.append(int(dest_id))
            except ValueError:
                # Keep as string if conversion fails
                processed_ids.append(dest_id)
        
        print(f"Processed IDs: {processed_ids}")  # Debug log
        
        # Fetch destinations including image_url
        result = supabase.table("destinasi").select(
            "destinasi_id, nama_destinasi, kategori_id, deskripsi, image_url"
        ).in_("destinasi_id", processed_ids).execute()
        
        print(f"Database query result: {result}")  # Debug log
        
        if result.data:
            destinations = []
            for destination in result.data:
                destinations.append({
                    "destinasi_id": str(destination["destinasi_id"]),  # Ensure string format
                    "nama_destinasi": destination["nama_destinasi"],
                    "kategori_id": destination["kategori_id"],
                    "deskripsi": destination["deskripsi"],
                    "image_url": destination.get("image_url"),
                    "category_name": None  # We'll add category lookup later if needed
                })
            print(f"Returning {len(destinations)} destinations")  # Debug log
            return destinations
        else:
            print("No destinations found in database")  # Debug log
            return []
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get destinations by IDs error: {str(e)}")
        print(f"Error type: {type(e)}")  # Debug log
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get destinations: {str(e)}"
        )
