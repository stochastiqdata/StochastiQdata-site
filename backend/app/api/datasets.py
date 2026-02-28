"""
Dataset API endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from app.core.database import get_supabase_client
from app.middleware.supabase_auth import SupabaseUser, get_current_user, require_auth
import uuid
import os
from app.schemas import (
    DatasetCreate,
    DatasetResponse,
    DatasetListResponse,
    DatasetSource,
    BusinessTag,
    ModelingType,
    PivotVariable,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    source: Optional[DatasetSource] = None,
    tags: Optional[List[BusinessTag]] = Query(None),
    modeling_types: Optional[List[ModelingType]] = Query(None),
    pivot_variables: Optional[List[PivotVariable]] = Query(None),
    search: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(global_score|created_at|name|review_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
):
    """
    List all datasets with filtering, pagination and sorting
    """
    supabase = get_supabase_client()

    # Build query
    query = supabase.table("datasets").select("*", count="exact")

    # Apply filters
    if source:
        query = query.eq("source", source.value)

    if tags:
        # Filter datasets that contain any of the specified tags
        query = query.contains("tags", [tag.value for tag in tags])

    if modeling_types:
        # Filter datasets that contain any of the specified modeling types
        query = query.contains("modeling_types", [mt.value for mt in modeling_types])

    if pivot_variables:
        # Filter datasets that contain any of the specified pivot variables
        query = query.contains("pivot_variables", [pv.value for pv in pivot_variables])

    if search:
        query = query.ilike("name", f"%{search}%")

    # Apply sorting
    query = query.order(sort_by, desc=(sort_order == "desc"))

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)

    # Execute query
    response = query.execute()

    return DatasetListResponse(
        datasets=[DatasetResponse(**d) for d in response.data],
        total=response.count or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str):
    """
    Get a single dataset by ID
    """
    supabase = get_supabase_client()

    response = supabase.table("datasets").select("*").eq("id", dataset_id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return DatasetResponse(**response.data)


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    dataset: DatasetCreate,
    current_user: SupabaseUser = Depends(get_current_user),  # Optionnel en mode démo
):
    """
    Create a new dataset (authentication optionnelle en mode démo)
    """
    supabase = get_supabase_client()

    data = dataset.model_dump()
    data["created_by"] = current_user.user_id if current_user else "anonymous"
    data["tags"] = [tag.value for tag in dataset.tags]
    data["source"] = dataset.source.value
    data["modeling_types"] = [mt.value for mt in dataset.modeling_types]
    data["pivot_variables"] = [pv.value for pv in dataset.pivot_variables]

    response = supabase.table("datasets").insert(data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create dataset")

    return DatasetResponse(**response.data[0])


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: str,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Delete a dataset (only by creator)
    """
    supabase = get_supabase_client()

    # Check ownership
    existing = supabase.table("datasets").select("created_by").eq("id", dataset_id).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if existing.data["created_by"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this dataset")

    supabase.table("datasets").delete().eq("id", dataset_id).execute()


@router.post("/upload")
async def upload_dataset_file(
    file: UploadFile = File(...),
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Upload a dataset file (CSV, Parquet, Excel) to Supabase Storage.
    Returns the public URL of the uploaded file.
    """
    ALLOWED_TYPES = [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    ]
    MAX_SIZE_MB = 50

    # Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".csv", ".parquet", ".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez CSV, Parquet ou Excel.")

    content = await file.read()

    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Fichier trop volumineux (max {MAX_SIZE_MB} MB).")

    supabase = get_supabase_client()

    # Unique filename to avoid collisions
    unique_name = f"{current_user.user_id}/{uuid.uuid4()}{ext}"

    try:
        supabase.storage.from_("datasets").upload(
            unique_name,
            content,
            {"content-type": file.content_type or "application/octet-stream"},
        )
        public_url = supabase.storage.from_("datasets").get_public_url(unique_name)
        return {
            "url": public_url,
            "filename": file.filename,
            "size_mb": round(len(content) / (1024 * 1024), 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload : {str(e)}")
