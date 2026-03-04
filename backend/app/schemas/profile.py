"""
Pydantic schemas for Profile
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    title: Optional[str] = Field(None, max_length=150, description="Ex: Actuaire FCAS, Data Scientist")
    organization: Optional[str] = Field(None, max_length=150)
    bio: Optional[str] = Field(None, max_length=500)


class ProfileResponse(BaseModel):
    id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    title: Optional[str] = None
    organization: Optional[str] = None
    bio: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
