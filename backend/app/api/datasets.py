"""
Dataset API endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from app.core.database import get_supabase_client, get_supabase_admin_client
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


@router.post("/{dataset_id}/upload-file")
async def upload_dataset_file(
    dataset_id: str,
    file: UploadFile = File(...),
    current_user: SupabaseUser = Depends(get_current_user),  # Optionnel en mode démo
):
    """
    Upload a dataset file (CSV, Parquet, Excel) to Supabase Storage.
    Updates the dataset record with the public URL.
    """
    ALLOWED_EXTENSIONS = [".csv", ".parquet", ".xlsx", ".xls"]
    MAX_SIZE_MB = 50

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez CSV, Parquet ou Excel.")

    content = await file.read()

    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Fichier trop volumineux (max {MAX_SIZE_MB} MB).")

    import hashlib
    from datetime import datetime, timezone

    supabase_admin = get_supabase_admin_client()
    file_path = f"{dataset_id}/{uuid.uuid4()}{ext}"

    # Calcul SHA256
    sha256 = hashlib.sha256(content).hexdigest()
    size_mb = round(len(content) / (1024 * 1024), 2)

    try:
        supabase_admin.storage.from_("datasets-files").upload(
            file_path,
            content,
            {"content-type": file.content_type or "application/octet-stream"},
        )
        public_url = supabase_admin.storage.from_("datasets-files").get_public_url(file_path)

        # Récupérer le changelog existant
        existing = supabase_admin.table("datasets").select("changelog").eq("id", dataset_id).single().execute()
        current_changelog = (existing.data or {}).get("changelog") or []
        version_num = len(current_changelog) + 1
        new_entry = {
            "version": f"v{version_num}.0",
            "date": datetime.now(timezone.utc).isoformat(),
            "description": f"Upload : {file.filename}",
            "file_url": public_url,
            "hash": sha256,
            "size_mb": size_mb,
        }
        current_changelog.append(new_entry)

        supabase_admin.table("datasets").update({
            "file_url": public_url,
            "file_hash": sha256,
            "changelog": current_changelog,
            "computed_cache": {},  # Invalider le cache stats/correlations
        }).eq("id", dataset_id).execute()

        return {
            "file_url": public_url,
            "filename": file.filename,
            "size_mb": size_mb,
            "sha256": sha256,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload : {str(e)}")

@router.get("/{dataset_id}/similar")
async def similar_datasets(dataset_id: str):
    """
    Retourne jusqu'à 4 datasets ayant des tags en commun avec le dataset donné.
    Triés par nombre de tags en commun décroissant.
    """
    supabase = get_supabase_client()

    result = supabase.table("datasets").select("tags").eq("id", dataset_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Dataset non trouvé.")

    tags = result.data.get("tags") or []

    if not tags:
        return {"datasets": [], "source_tags": []}

    similar = (
        supabase.table("datasets")
        .select("id, name, global_score, tags, modeling_types, file_url, download_count, review_count, file_size_mb")
        .neq("id", dataset_id)
        .overlaps("tags", tags)
        .limit(20)
        .execute()
    )

    def common_count(d):
        return len(set(tags) & set(d.get("tags") or []))

    sorted_datasets = sorted(similar.data or [], key=common_count, reverse=True)[:4]

    return {"datasets": sorted_datasets, "source_tags": tags}


@router.post("/{dataset_id}/download")
async def download_dataset(dataset_id: str):
    """
    Incrémente le compteur de téléchargements et retourne l'URL du fichier.
    """
    supabase = get_supabase_client()
    supabase_admin = get_supabase_admin_client()

    result = supabase.table("datasets").select("file_url, download_count").eq("id", dataset_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Dataset non trouvé.")

    if not result.data.get("file_url"):
        raise HTTPException(status_code=404, detail="Aucun fichier disponible pour ce dataset.")

    new_count = (result.data.get("download_count") or 0) + 1
    supabase_admin.table("datasets").update({"download_count": new_count}).eq("id", dataset_id).execute()

    return {"file_url": result.data["file_url"], "download_count": new_count}


@router.get("/{dataset_id}/preview")
async def preview_dataset(dataset_id: str):
    """
    Retourne les 10 premières lignes du fichier CSV hébergé sur Supabase.
    """
    import pandas as pd
    import io
    import httpx

    supabase = get_supabase_client()
    result = supabase.table("datasets").select("file_url").eq("id", dataset_id).single().execute()

    if not result.data or not result.data.get("file_url"):
        raise HTTPException(status_code=404, detail="Aucun fichier disponible pour ce dataset.")

    file_url = result.data["file_url"]

    try:
        ext = os.path.splitext(file_url.split("?")[0])[1].lower()

        # Pour les CSV, télécharger seulement les 512 premiers KB (largement suffisant pour 10 lignes)
        async with httpx.AsyncClient() as client:
            if ext in (".csv", ""):
                response = await client.get(
                    file_url,
                    headers={"Range": "bytes=0-524287"},
                    timeout=20,
                )
            else:
                response = await client.get(file_url, timeout=30)

        content = response.content

        if ext == ".csv" or ext == "":
            df = pd.read_csv(io.BytesIO(content), nrows=10, on_bad_lines="skip")
        elif ext == ".parquet":
            df = pd.read_parquet(io.BytesIO(content)).head(10)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(content), nrows=10)
        else:
            df = pd.read_csv(io.BytesIO(content), nrows=10, on_bad_lines="skip")

        columns = [{"name": col, "type": str(df[col].dtype)} for col in df.columns]
        rows = df.fillna("").astype(str).values.tolist()

        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture fichier : {str(e)}")


@router.get("/{dataset_id}/correlations")
async def correlations_dataset(dataset_id: str):
    """
    Retourne la matrice de corrélation entre les colonnes numériques.
    """
    import pandas as pd
    import io
    import httpx
    import math

    supabase = get_supabase_client()
    result = supabase.table("datasets").select("file_url, computed_cache").eq("id", dataset_id).single().execute()

    if not result.data or not result.data.get("file_url"):
        raise HTTPException(status_code=404, detail="Aucun fichier disponible pour ce dataset.")

    # Retourner le cache si disponible
    cached = (result.data.get("computed_cache") or {}).get("correlations")
    if cached:
        return cached

    file_url = result.data["file_url"]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url, timeout=90)
            response.raise_for_status()

        ext = os.path.splitext(file_url.split("?")[0])[1].lower()
        content = response.content

        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        elif ext == ".parquet":
            df = pd.read_parquet(io.BytesIO(content))
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))

        numeric_df = df.select_dtypes(include=["number"])

        if numeric_df.shape[1] < 2:
            raise HTTPException(status_code=422, detail="Pas assez de colonnes numériques pour calculer les corrélations.")

        corr = numeric_df.corr()

        def safe_corr(v):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                return None
            return round(float(v), 3)

        columns = corr.columns.tolist()
        matrix = [[safe_corr(corr.loc[r, c]) for c in columns] for r in columns]
        payload = {"columns": columns, "matrix": matrix}

        # Stocker en cache
        existing_cache = result.data.get("computed_cache") or {}
        existing_cache["correlations"] = payload
        get_supabase_admin_client().table("datasets").update({"computed_cache": existing_cache}).eq("id", dataset_id).execute()

        return payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur calcul corrélations : {str(e)}")


@router.get("/{dataset_id}/stats")
async def stats_dataset(dataset_id: str):
    """
    Calcule les statistiques complètes du dataset (profil global + stats par colonne).
    """
    import pandas as pd
    import io
    import httpx
    import math
    import numpy as np

    supabase = get_supabase_client()
    result = supabase.table("datasets").select("file_url, computed_cache").eq("id", dataset_id).single().execute()

    if not result.data or not result.data.get("file_url"):
        raise HTTPException(status_code=404, detail="Aucun fichier disponible pour ce dataset.")

    # Retourner le cache si disponible
    cached = (result.data.get("computed_cache") or {}).get("stats")
    if cached:
        return cached

    file_url = result.data["file_url"]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url, timeout=90)
            response.raise_for_status()

        ext = os.path.splitext(file_url.split("?")[0])[1].lower()
        content = response.content

        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        elif ext == ".parquet":
            df = pd.read_parquet(io.BytesIO(content))
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))

        total_rows, total_cols = df.shape
        total_cells = total_rows * total_cols
        total_nulls = int(df.isnull().sum().sum())
        overall_null_pct = round(total_nulls / total_cells * 100, 1) if total_cells > 0 else 0

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

        # Statistiques par colonne
        columns_stats = []
        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            null_pct = round(null_count / total_rows * 100, 1) if total_rows > 0 else 0
            unique = int(df[col].nunique())
            is_numeric = col in numeric_cols

            stat = {
                "name": col,
                "dtype": str(df[col].dtype),
                "is_numeric": is_numeric,
                "null_count": null_count,
                "null_pct": null_pct,
                "unique": unique,
            }

            if is_numeric:
                s = df[col].dropna()
                def safe(v):
                    return None if (v is None or (isinstance(v, float) and math.isnan(v))) else round(float(v), 4)
                stat.update({
                    "mean": safe(s.mean()),
                    "std": safe(s.std()),
                    "min": safe(s.min()),
                    "p25": safe(s.quantile(0.25)),
                    "p50": safe(s.quantile(0.50)),
                    "p75": safe(s.quantile(0.75)),
                    "max": safe(s.max()),
                })
                if len(s) > 1:
                    n_bins = min(30, max(5, unique))
                    counts, edges = np.histogram(s, bins=n_bins)
                    stat["histogram"] = {
                        "counts": counts.tolist(),
                        "edges": [round(float(e), 4) for e in edges.tolist()],
                    }
            else:
                top = df[col].value_counts().head(10)
                stat["top_values"] = [{"value": str(k), "count": int(v)} for k, v in top.items()]

            columns_stats.append(stat)

        # Profil global — détection variable cible
        suggested_target = None
        for candidate in ["ClaimNb", "claim_nb", "target", "label", "y", "income", "churn", "default"]:
            if candidate in df.columns:
                suggested_target = candidate
                break

        payload = {
            "profile": {
                "total_rows": total_rows,
                "total_cols": total_cols,
                "overall_null_pct": overall_null_pct,
                "numeric_count": len(numeric_cols),
                "categorical_count": len(categorical_cols),
                "suggested_target": suggested_target,
            },
            "columns": columns_stats,
        }

        # Stocker en cache
        existing_cache = result.data.get("computed_cache") or {}
        existing_cache["stats"] = payload
        get_supabase_admin_client().table("datasets").update({"computed_cache": existing_cache}).eq("id", dataset_id).execute()

        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur calcul stats : {str(e)}")