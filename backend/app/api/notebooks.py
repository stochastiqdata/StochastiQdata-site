"""
Notebook API endpoints - Linked scripts and analyses
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_supabase_client
from app.middleware.supabase_auth import SupabaseUser, require_auth
from app.schemas import NotebookCreate, NotebookUpdate, NotebookResponse

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


@router.get("/dataset/{dataset_id}", response_model=List[NotebookResponse])
async def list_notebooks_for_dataset(dataset_id: str):
    """
    Get all notebooks linked to a specific dataset
    """
    supabase = get_supabase_client()

    response = (
        supabase.table("notebooks")
        .select("*")
        .eq("dataset_id", dataset_id)
        .order("created_at", desc=True)
        .execute()
    )

    return [NotebookResponse(**n) for n in response.data]


@router.get("/user/me", response_model=List[NotebookResponse])
async def get_my_notebooks(current_user: SupabaseUser = Depends(require_auth)):
    """
    Get all notebooks created by the current user
    """
    supabase = get_supabase_client()

    response = (
        supabase.table("notebooks")
        .select("*")
        .eq("user_id", current_user.user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return [NotebookResponse(**n) for n in response.data]


@router.post("", response_model=NotebookResponse, status_code=201)
async def create_notebook(
    notebook: NotebookCreate,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Create a new notebook link for a dataset (requires authentication)
    """
    supabase = get_supabase_client()

    # Check if dataset exists
    dataset = supabase.table("datasets").select("id").eq("id", notebook.dataset_id).single().execute()

    if not dataset.data:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Create notebook
    data = {
        "dataset_id": notebook.dataset_id,
        "user_id": current_user.user_id,
        "title": notebook.title,
        "url": notebook.url,
        "platform": notebook.get_platform().value,
        "description": notebook.description,
    }

    response = supabase.table("notebooks").insert(data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create notebook")

    return NotebookResponse(**response.data[0])


@router.put("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(
    notebook_id: str,
    notebook: NotebookUpdate,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Update an existing notebook (only by the author)
    """
    supabase = get_supabase_client()

    # Check ownership
    existing = supabase.table("notebooks").select("*").eq("id", notebook_id).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Notebook not found")

    if existing.data["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this notebook")

    # Update only provided fields
    update_data = notebook.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Convert platform enum to string if present
    if "platform" in update_data and update_data["platform"]:
        update_data["platform"] = update_data["platform"].value

    response = supabase.table("notebooks").update(update_data).eq("id", notebook_id).execute()

    return NotebookResponse(**response.data[0])


@router.delete("/{notebook_id}", status_code=204)
async def delete_notebook(
    notebook_id: str,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Delete a notebook (only by the author)
    """
    supabase = get_supabase_client()

    # Check ownership
    existing = supabase.table("notebooks").select("user_id").eq("id", notebook_id).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Notebook not found")

    if existing.data["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this notebook")

    supabase.table("notebooks").delete().eq("id", notebook_id).execute()
