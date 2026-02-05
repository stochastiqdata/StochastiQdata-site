"""
Review API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_supabase_client
from app.middleware.supabase_auth import SupabaseUser, get_current_user, require_auth
from app.schemas import ReviewCreate, ReviewUpdate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/dataset/{dataset_id}", response_model=List[ReviewResponse])
async def list_reviews_for_dataset(dataset_id: str):
    """
    Get all reviews for a specific dataset
    """
    supabase = get_supabase_client()

    response = (
        supabase.table("reviews")
        .select("*")
        .eq("dataset_id", dataset_id)
        .order("created_at", desc=True)
        .execute()
    )

    return [ReviewResponse(**r) for r in response.data]


@router.get("/user/me", response_model=List[ReviewResponse])
async def get_my_reviews(current_user: SupabaseUser = Depends(require_auth)):
    """
    Get all reviews by the current authenticated user
    """
    supabase = get_supabase_client()

    response = (
        supabase.table("reviews")
        .select("*")
        .eq("user_id", current_user.user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return [ReviewResponse(**r) for r in response.data]


@router.post("", response_model=ReviewResponse, status_code=201)
async def create_review(
    review: ReviewCreate,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Create a new review for a dataset (requires authentication)
    One review per user per dataset
    """
    supabase = get_supabase_client()

    # Check if dataset exists
    dataset = supabase.table("datasets").select("id").eq("id", review.dataset_id).single().execute()

    if not dataset.data:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Check if user already reviewed this dataset
    existing = (
        supabase.table("reviews")
        .select("id")
        .eq("dataset_id", review.dataset_id)
        .eq("user_id", current_user.user_id)
        .execute()
    )

    if existing.data:
        raise HTTPException(
            status_code=409,
            detail="You have already reviewed this dataset. Use PUT to update.",
        )

    # Create review
    data = review.model_dump()
    data["user_id"] = current_user.user_id

    response = supabase.table("reviews").insert(data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create review")

    return ReviewResponse(**response.data[0])


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    review: ReviewUpdate,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Update an existing review (only by the author)
    """
    supabase = get_supabase_client()

    # Check ownership
    existing = supabase.table("reviews").select("*").eq("id", review_id).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Review not found")

    if existing.data["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this review")

    # Update only provided fields
    update_data = review.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    response = supabase.table("reviews").update(update_data).eq("id", review_id).execute()

    return ReviewResponse(**response.data[0])


@router.delete("/{review_id}", status_code=204)
async def delete_review(
    review_id: str,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Delete a review (only by the author)
    """
    supabase = get_supabase_client()

    # Check ownership
    existing = supabase.table("reviews").select("user_id").eq("id", review_id).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Review not found")

    if existing.data["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")

    supabase.table("reviews").delete().eq("id", review_id).execute()
