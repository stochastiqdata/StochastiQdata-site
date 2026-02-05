"""
Pydantic schemas for Benchmark (SOTA performance tracking)
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from .dataset import ModelType, MetricType


class BenchmarkBase(BaseModel):
    model_type: ModelType
    model_name: Optional[str] = Field(None, max_length=255, description="Nom personnalisé du modèle")
    metric_type: MetricType
    metric_value: float = Field(..., description="Valeur de la métrique")
    notebook_url: Optional[str] = Field(None, max_length=500, description="Lien vers le notebook/code")
    methodology: Optional[str] = Field(None, description="Description de la méthodologie utilisée")


class BenchmarkCreate(BenchmarkBase):
    dataset_id: str


class BenchmarkUpdate(BaseModel):
    model_name: Optional[str] = None
    metric_value: Optional[float] = None
    notebook_url: Optional[str] = None
    methodology: Optional[str] = None


class BenchmarkResponse(BenchmarkBase):
    id: str
    dataset_id: str
    user_id: str
    is_verified: bool = False
    upvotes: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BenchmarkListResponse(BaseModel):
    benchmarks: List[BenchmarkResponse]
    total: int


class BenchmarkLeaderboard(BaseModel):
    """Leaderboard pour une métrique spécifique sur un dataset"""
    dataset_id: str
    metric_type: MetricType
    entries: List[BenchmarkResponse]
