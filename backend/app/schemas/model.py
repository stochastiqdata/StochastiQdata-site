"""
Pydantic schemas for Model
"""
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class ModelCreate(BaseModel):
    dataset_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    model_type: str = Field(..., description="Type: glm, xgboost, random_forest, neural_network, etc.")
    family: Optional[str] = Field(None, description="Famille GLM: poisson, gamma, gaussian, binomial, tweedie")
    link_function: Optional[str] = Field(None, description="Lien GLM: log, identity, logit, sqrt")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Hyperparamètres du modèle")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Métriques d'évaluation")
    code_snippet: Optional[str] = Field(None, description="Extrait de code Python/R")
    notebook_url: Optional[str] = Field(None, description="URL vers le notebook complet")
    model_file_url: Optional[str] = Field(None, description="URL du fichier modèle (.pkl, .joblib, .rds)")
    tags: List[str] = Field(default_factory=list)


class ModelResponse(ModelCreate):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
