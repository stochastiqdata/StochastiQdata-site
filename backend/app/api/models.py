"""
Model API endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from app.core.database import get_supabase_client, get_supabase_admin_client
from app.middleware.supabase_auth import get_current_user, SupabaseUser
from app.schemas.model import ModelCreate, ModelResponse

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=List[ModelResponse])
async def list_models(dataset_id: Optional[str] = Query(None)):
    """
    List models, optionally filtered by dataset_id.
    """
    supabase = get_supabase_client()
    query = supabase.table("models").select("*")
    if dataset_id:
        query = query.eq("dataset_id", dataset_id)
    response = query.order("created_at", desc=True).execute()
    return [ModelResponse(**m) for m in (response.data or [])]


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str):
    """
    Get a single model by ID.
    """
    supabase = get_supabase_client()
    response = supabase.table("models").select("*").eq("id", model_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Modèle non trouvé.")
    return ModelResponse(**response.data)


@router.post("", response_model=ModelResponse, status_code=201)
async def create_model(
    model: ModelCreate,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """
    Create a new model affiliated to a dataset.
    """
    supabase = get_supabase_client()
    supabase_admin = get_supabase_admin_client()

    # Verify dataset exists
    ds = supabase.table("datasets").select("id").eq("id", model.dataset_id).single().execute()
    if not ds.data:
        raise HTTPException(status_code=404, detail="Dataset non trouvé.")

    data = model.model_dump()
    data["created_by"] = current_user.user_id if current_user else "anonymous"

    response = supabase_admin.table("models").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Erreur lors de la création du modèle.")

    return ModelResponse(**response.data[0])


@router.delete("/{model_id}", status_code=204)
async def delete_model(
    model_id: str,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """
    Delete a model (only by creator).
    """
    supabase = get_supabase_client()
    supabase_admin = get_supabase_admin_client()

    existing = supabase.table("models").select("created_by").eq("id", model_id).single().execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Modèle non trouvé.")

    if existing.data["created_by"] != (current_user.user_id if current_user else None):
        raise HTTPException(status_code=403, detail="Non autorisé.")

    supabase_admin.table("models").delete().eq("id", model_id).execute()
