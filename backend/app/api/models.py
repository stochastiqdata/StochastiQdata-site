"""
Model API endpoints
"""
import os
import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from app.core.database import get_supabase_client, get_supabase_admin_client
from app.middleware.supabase_auth import get_current_user, SupabaseUser
from app.schemas.model import ModelCreate, ModelResponse
from app.api.profiles import upsert_profile_from_user

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

    # Auto-create profile from JWT data on first model submission
    if current_user:
        upsert_profile_from_user(current_user, supabase_admin)

    response = supabase_admin.table("models").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Erreur lors de la création du modèle.")

    return ModelResponse(**response.data[0])


@router.post("/{model_id}/upload-file")
async def upload_model_file(
    model_id: str,
    file: UploadFile = File(...),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """
    Upload a model file (.pkl, .joblib, .rds, .h5) to Supabase Storage.
    Updates the model record with the public URL.
    """
    ALLOWED_EXTENSIONS = [".pkl", ".joblib", ".rds", ".h5", ".pt", ".onnx", ".zip"]
    MAX_SIZE_MB = 200

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté. Formats acceptés : {', '.join(ALLOWED_EXTENSIONS)}"
        )

    content = await file.read()
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Fichier trop volumineux (max {MAX_SIZE_MB} MB).")

    supabase = get_supabase_client()
    supabase_admin = get_supabase_admin_client()

    # Verify model exists and belongs to current user
    existing = supabase.table("models").select("id, created_by").eq("id", model_id).single().execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Modèle non trouvé.")
    if existing.data["created_by"] != (current_user.user_id if current_user else None):
        raise HTTPException(status_code=403, detail="Non autorisé.")

    file_path = f"{model_id}/{uuid.uuid4()}{ext}"

    try:
        supabase_admin.storage.from_("models-files").upload(
            file_path,
            content,
            {"content-type": file.content_type or "application/octet-stream"},
        )
        public_url = supabase_admin.storage.from_("models-files").get_public_url(file_path)

        supabase_admin.table("models").update({
            "model_file_url": public_url,
        }).eq("id", model_id).execute()

        return {
            "model_file_url": public_url,
            "filename": file.filename,
            "size_mb": round(len(content) / (1024 * 1024), 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload : {str(e)}")


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
