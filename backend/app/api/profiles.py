"""
Profile API endpoints
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from app.core.database import get_supabase_client, get_supabase_admin_client
from app.middleware.supabase_auth import get_current_user, SupabaseUser
from app.schemas.profile import ProfileUpdate, ProfileResponse

router = APIRouter(prefix="/profiles", tags=["profiles"])


def upsert_profile_from_user(user: SupabaseUser, admin_client=None):
    """
    Upsert a profile row from JWT user data.
    Called on first model submission to auto-create the profile.
    """
    if not user:
        return
    client = admin_client or get_supabase_admin_client()
    data = {"id": user.user_id}
    if user.full_name:
        data["display_name"] = user.full_name
    elif user.first_name or user.last_name:
        data["display_name"] = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if user.avatar_url:
        data["avatar_url"] = user.avatar_url
    client.table("profiles").upsert(data, on_conflict="id", ignore_duplicates=True).execute()


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str):
    """
    Get a public profile by user_id.
    """
    supabase = get_supabase_client()
    response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Profil non trouvé.")
    return ProfileResponse(**response.data)


@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    data: ProfileUpdate,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """
    Create or update the authenticated user's profile.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentification requise.")

    supabase_admin = get_supabase_admin_client()
    payload = {"id": current_user.user_id}
    payload.update({k: v for k, v in data.model_dump().items() if v is not None})

    response = supabase_admin.table("profiles").upsert(payload, on_conflict="id").execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du profil.")
    return ProfileResponse(**response.data[0])


@router.get("/{user_id}/models")
async def get_profile_models(user_id: str):
    """
    Get all models submitted by a user.
    """
    supabase = get_supabase_client()
    response = supabase.table("models").select("*").eq("created_by", user_id).order("created_at", desc=True).execute()
    return response.data or []
