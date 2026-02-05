"""
Benchmark API endpoints - SOTA performance tracking
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.database import get_supabase_client
from app.middleware.supabase_auth import SupabaseUser, require_auth
from app.schemas import (
    BenchmarkCreate,
    BenchmarkUpdate,
    BenchmarkResponse,
    BenchmarkListResponse,
    ModelType,
    MetricType,
)

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.get("/dataset/{dataset_id}", response_model=BenchmarkListResponse)
async def list_benchmarks_for_dataset(
    dataset_id: str,
    model_type: Optional[ModelType] = None,
    metric_type: Optional[MetricType] = None,
    sort_by: str = Query("metric_value", enum=["metric_value", "created_at", "upvotes"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
):
    """
    Get all benchmarks for a specific dataset with optional filtering
    """
    supabase = get_supabase_client()

    query = supabase.table("benchmarks").select("*").eq("dataset_id", dataset_id)

    if model_type:
        query = query.eq("model_type", model_type.value)

    if metric_type:
        query = query.eq("metric_type", metric_type.value)

    response = query.order(sort_by, desc=(sort_order == "desc")).execute()

    benchmarks = [BenchmarkResponse(**b) for b in response.data]
    return BenchmarkListResponse(benchmarks=benchmarks, total=len(benchmarks))


@router.get("/dataset/{dataset_id}/leaderboard", response_model=List[BenchmarkResponse])
async def get_leaderboard(
    dataset_id: str,
    metric_type: MetricType,
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get the leaderboard (best scores) for a specific metric on a dataset
    """
    supabase = get_supabase_client()

    # For most metrics, lower is better (RMSE, MAE, etc.)
    # For Gini, AUC, R2, accuracy, f1_score - higher is better
    higher_is_better = metric_type in [
        MetricType.GINI,
        MetricType.AUC,
        MetricType.R2,
        MetricType.ACCURACY,
        MetricType.F1_SCORE,
    ]

    response = (
        supabase.table("benchmarks")
        .select("*")
        .eq("dataset_id", dataset_id)
        .eq("metric_type", metric_type.value)
        .order("metric_value", desc=higher_is_better)
        .limit(limit)
        .execute()
    )

    return [BenchmarkResponse(**b) for b in response.data]


@router.get("/user/me", response_model=List[BenchmarkResponse])
async def get_my_benchmarks(current_user: SupabaseUser = Depends(require_auth)):
    """
    Get all benchmarks created by the current user
    """
    supabase = get_supabase_client()

    response = (
        supabase.table("benchmarks")
        .select("*")
        .eq("user_id", current_user.user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return [BenchmarkResponse(**b) for b in response.data]


@router.get("/{benchmark_id}", response_model=BenchmarkResponse)
async def get_benchmark(benchmark_id: str):
    """
    Get a specific benchmark by ID
    """
    supabase = get_supabase_client()

    response = supabase.table("benchmarks").select("*").eq("id", benchmark_id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    return BenchmarkResponse(**response.data)


@router.post("", response_model=BenchmarkResponse, status_code=201)
async def create_benchmark(
    benchmark: BenchmarkCreate,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Create a new benchmark entry (requires authentication)
    """
    supabase = get_supabase_client()

    # Check if dataset exists
    dataset = supabase.table("datasets").select("id").eq("id", benchmark.dataset_id).single().execute()

    if not dataset.data:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Create benchmark
    data = {
        "dataset_id": benchmark.dataset_id,
        "user_id": current_user.user_id,
        "model_type": benchmark.model_type.value,
        "model_name": benchmark.model_name,
        "metric_type": benchmark.metric_type.value,
        "metric_value": benchmark.metric_value,
        "notebook_url": benchmark.notebook_url,
        "methodology": benchmark.methodology,
    }

    response = supabase.table("benchmarks").insert(data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create benchmark")

    return BenchmarkResponse(**response.data[0])


@router.put("/{benchmark_id}", response_model=BenchmarkResponse)
async def update_benchmark(
    benchmark_id: str,
    benchmark: BenchmarkUpdate,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Update an existing benchmark (only by the author)
    """
    supabase = get_supabase_client()

    # Check ownership
    existing = supabase.table("benchmarks").select("*").eq("id", benchmark_id).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    if existing.data["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this benchmark")

    # Update only provided fields
    update_data = benchmark.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    response = supabase.table("benchmarks").update(update_data).eq("id", benchmark_id).execute()

    return BenchmarkResponse(**response.data[0])


@router.delete("/{benchmark_id}", status_code=204)
async def delete_benchmark(
    benchmark_id: str,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Delete a benchmark (only by the author)
    """
    supabase = get_supabase_client()

    # Check ownership
    existing = supabase.table("benchmarks").select("user_id").eq("id", benchmark_id).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    if existing.data["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this benchmark")

    supabase.table("benchmarks").delete().eq("id", benchmark_id).execute()


@router.post("/{benchmark_id}/upvote", response_model=BenchmarkResponse)
async def upvote_benchmark(
    benchmark_id: str,
    current_user: SupabaseUser = Depends(require_auth),
):
    """
    Upvote a benchmark entry
    """
    supabase = get_supabase_client()

    # Get current benchmark
    existing = supabase.table("benchmarks").select("*").eq("id", benchmark_id).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    # Increment upvotes
    new_upvotes = existing.data.get("upvotes", 0) + 1

    response = (
        supabase.table("benchmarks")
        .update({"upvotes": new_upvotes})
        .eq("id", benchmark_id)
        .execute()
    )

    return BenchmarkResponse(**response.data[0])
