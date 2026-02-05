"""
Configuration settings for StochastiQdata Backend
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    supabase_jwt_secret: str  # JWT secret from Supabase dashboard

    # CORS
    frontend_url: str = "http://localhost:3000"

    # App
    app_name: str = "StochastiQdata API"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
