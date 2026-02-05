"""
Pydantic schemas for Notebook (linked scripts/analyses)
"""
from typing import Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


class NotebookPlatform(str, Enum):
    GITHUB = "github"
    KAGGLE = "kaggle"
    COLAB = "colab"
    OTHER = "other"


def detect_platform(url: str) -> NotebookPlatform:
    """Auto-detect platform from URL"""
    url_lower = url.lower()
    if "github.com" in url_lower or "raw.githubusercontent.com" in url_lower:
        return NotebookPlatform.GITHUB
    elif "kaggle.com" in url_lower:
        return NotebookPlatform.KAGGLE
    elif "colab.research.google.com" in url_lower or "colab.google" in url_lower:
        return NotebookPlatform.COLAB
    return NotebookPlatform.OTHER


class NotebookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., max_length=500)
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        # Basic URL validation
        url_pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        if not url_pattern.match(v):
            raise ValueError("Invalid URL format")
        return v


class NotebookCreate(NotebookBase):
    dataset_id: str
    platform: Optional[NotebookPlatform] = None  # Auto-detected if not provided

    def get_platform(self) -> NotebookPlatform:
        """Get platform, auto-detecting from URL if not specified"""
        if self.platform:
            return self.platform
        return detect_platform(self.url)


class NotebookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=1000)
    platform: Optional[NotebookPlatform] = None


class NotebookResponse(NotebookBase):
    id: str
    dataset_id: str
    user_id: str
    platform: NotebookPlatform
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
