"""
Favorites API endpoints
Permet aux utilisateurs de gérer leurs datasets favoris
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.database import get_supabase_client
from app.middleware.supabase_auth import SupabaseUser, require_auth, get_current_user
from app.schemas import DatasetResponse

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoriteResponse(BaseModel):
    """Response for favorite operations"""
    success: bool
    message: str
    is_favorite: bool


class FavoriteStatus(BaseModel):
    """Status of a favorite"""
    dataset_id: str
    is_favorite: bool


@router.get("", response_model=List[DatasetResponse])
async def list_favorites(
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Liste tous les datasets favoris de l'utilisateur connecté
    """
    supabase = get_supabase_client()

    # Récupérer les IDs des favoris
    favorites_response = supabase.table("user_favorites")\
        .select("dataset_id")\
        .eq("user_id", current_user.user_id)\
        .execute()

    if not favorites_response.data:
        return []

    # Récupérer les datasets correspondants
    dataset_ids = [f["dataset_id"] for f in favorites_response.data]

    datasets_response = supabase.table("datasets")\
        .select("*")\
        .in_("id", dataset_ids)\
        .execute()

    return [DatasetResponse(**d) for d in datasets_response.data]


@router.get("/check/{dataset_id}", response_model=FavoriteStatus)
async def check_favorite(
    dataset_id: str,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """
    Vérifie si un dataset est dans les favoris de l'utilisateur
    """
    if not current_user:
        return FavoriteStatus(dataset_id=dataset_id, is_favorite=False)

    supabase = get_supabase_client()

    response = supabase.table("user_favorites")\
        .select("id")\
        .eq("user_id", current_user.user_id)\
        .eq("dataset_id", dataset_id)\
        .execute()

    return FavoriteStatus(
        dataset_id=dataset_id,
        is_favorite=len(response.data) > 0
    )


@router.post("/{dataset_id}", response_model=FavoriteResponse)
async def add_favorite(
    dataset_id: str,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Ajoute un dataset aux favoris
    """
    supabase = get_supabase_client()

    # Vérifier que le dataset existe
    dataset = supabase.table("datasets")\
        .select("id")\
        .eq("id", dataset_id)\
        .single()\
        .execute()

    if not dataset.data:
        raise HTTPException(status_code=404, detail="Dataset non trouvé")

    # Vérifier si déjà en favoris
    existing = supabase.table("user_favorites")\
        .select("id")\
        .eq("user_id", current_user.user_id)\
        .eq("dataset_id", dataset_id)\
        .execute()

    if existing.data:
        return FavoriteResponse(
            success=True,
            message="Déjà dans vos favoris",
            is_favorite=True
        )

    # Ajouter aux favoris
    supabase.table("user_favorites").insert({
        "user_id": current_user.user_id,
        "dataset_id": dataset_id
    }).execute()

    return FavoriteResponse(
        success=True,
        message="Ajouté aux favoris",
        is_favorite=True
    )


@router.delete("/{dataset_id}", response_model=FavoriteResponse)
async def remove_favorite(
    dataset_id: str,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Retire un dataset des favoris
    """
    supabase = get_supabase_client()

    supabase.table("user_favorites")\
        .delete()\
        .eq("user_id", current_user.user_id)\
        .eq("dataset_id", dataset_id)\
        .execute()

    return FavoriteResponse(
        success=True,
        message="Retiré des favoris",
        is_favorite=False
    )


@router.post("/{dataset_id}/toggle", response_model=FavoriteResponse)
async def toggle_favorite(
    dataset_id: str,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Toggle un dataset dans les favoris (ajoute si absent, retire si présent)
    """
    supabase = get_supabase_client()

    # Vérifier que le dataset existe
    dataset = supabase.table("datasets")\
        .select("id")\
        .eq("id", dataset_id)\
        .single()\
        .execute()

    if not dataset.data:
        raise HTTPException(status_code=404, detail="Dataset non trouvé")

    # Vérifier si déjà en favoris
    existing = supabase.table("user_favorites")\
        .select("id")\
        .eq("user_id", current_user.user_id)\
        .eq("dataset_id", dataset_id)\
        .execute()

    if existing.data:
        # Retirer des favoris
        supabase.table("user_favorites")\
            .delete()\
            .eq("user_id", current_user.user_id)\
            .eq("dataset_id", dataset_id)\
            .execute()

        return FavoriteResponse(
            success=True,
            message="Retiré des favoris",
            is_favorite=False
        )
    else:
        # Ajouter aux favoris
        supabase.table("user_favorites").insert({
            "user_id": current_user.user_id,
            "dataset_id": dataset_id
        }).execute()

        return FavoriteResponse(
            success=True,
            message="Ajouté aux favoris",
            is_favorite=True
        )
