"""
Pydantic schemas for Dataset
"""
from typing import Optional, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class DatasetSource(str, Enum):
    KAGGLE = "kaggle"
    INSEE = "insee"
    OPENDATA = "opendata"
    OTHER = "other"


class BusinessTag(str, Enum):
    IARD = "iard"
    SANTE = "sante"
    VIE = "vie"
    GLM = "glm"
    PRICING = "pricing"
    RESERVING = "reserving"
    FRAUDE = "fraude"
    MACHINE_LEARNING = "machine_learning"


class ModelingType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    TIME_SERIES = "time_series"
    CLUSTERING = "clustering"
    SURVIVAL = "survival"
    OTHER = "other"


class PivotVariable(str, Enum):
    OCCURRENCE_DATE = "occurrence_date"
    CLAIM_AMOUNT = "claim_amount"
    EXPOSURE = "exposure"
    POLICY_ID = "policy_id"
    CLAIM_ID = "claim_id"


class ModelType(str, Enum):
    GLM = "glm"
    XGBOOST = "xgboost"
    RANDOM_FOREST = "random_forest"
    CHAIN_LADDER = "chain_ladder"
    BORNHUETTER_FERGUSON = "bornhuetter_ferguson"
    MACK = "mack"
    COX = "cox"
    KAPLAN_MEIER = "kaplan_meier"
    NEURAL_NETWORK = "neural_network"
    LIGHTGBM = "lightgbm"
    CATBOOST = "catboost"
    OTHER = "other"


class MetricType(str, Enum):
    GINI = "gini"
    RMSE = "rmse"
    MAE = "mae"
    AIC = "aic"
    BIC = "bic"
    R2 = "r2"
    LOG_LOSS = "log_loss"
    AUC = "auc"
    ACCURACY = "accuracy"
    F1_SCORE = "f1_score"
    MAPE = "mape"
    OTHER = "other"


class DatasetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source: DatasetSource = DatasetSource.OTHER
    source_url: Optional[str] = None
    tags: List[BusinessTag] = []
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    file_size_mb: Optional[float] = None
    data_updated_at: Optional[datetime] = Field(None, description="Date de dernière mise à jour des données source")
    data_dictionary_url: Optional[str] = Field(None, description="URL vers le dictionnaire des variables")
    modeling_types: List[ModelingType] = Field(default=[], description="Types de modélisation supportés")
    pivot_variables: List[PivotVariable] = Field(default=[], description="Variables pivots disponibles")
    best_fit_models: List[ModelType] = Field(default=[], description="Modèles suggérés pour ce dataset")


class DatasetCreate(DatasetBase):
    pass


class DatasetResponse(DatasetBase):
    id: str
    avg_utility_score: float = 0
    avg_cleanliness_score: float = 0
    avg_documentation_score: float = 0
    global_score: float = 0
    review_count: int = 0
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
    total: int
    page: int
    page_size: int
