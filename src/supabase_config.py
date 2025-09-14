"""Конфигурация Supabase."""

from pydantic_settings import BaseSettings
from typing import Optional


class SupabaseSettings(BaseSettings):
    """Настройки Supabase."""
    
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_prefix = "SUPABASE_"
        extra = "ignore"


# Глобальные настройки Supabase
supabase_settings = SupabaseSettings()
