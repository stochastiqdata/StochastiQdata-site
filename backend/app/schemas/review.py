"""
Pydantic schemas for Review
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ReviewBase(BaseModel):
    utility_score: int = Field(..., ge=0, le=10, description="Utilité Actuarielle (0-10)")
    cleanliness_score: int = Field(..., ge=0, le=10, description="Propreté/Biais (0-10)")
    documentation_score: int = Field(..., ge=0, le=10, description="Documentation (0-10)")
    comment: Optional[str] = Field(None, max_length=2000)


class ReviewCreate(ReviewBase):
    dataset_id: str


class ReviewUpdate(BaseModel):
    utility_score: Optional[int] = Field(None, ge=0, le=10)
    cleanliness_score: Optional[int] = Field(None, ge=0, le=10)
    documentation_score: Optional[int] = Field(None, ge=0, le=10)
    comment: Optional[str] = Field(None, max_length=2000)


class ReviewResponse(ReviewBase):
    id: str
    dataset_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
