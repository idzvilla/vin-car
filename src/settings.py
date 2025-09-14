"""Настройки приложения."""

from __future__ import annotations

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""
    
    model_config = SettingsConfigDict(
        env_file="env_config",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Telegram Bot Configuration
    bot_token: str = Field(..., description="Токен Telegram бота")
    manager_chat_id: int = Field(..., description="ID чата менеджеров")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./vin_reports.db",
        description="URL подключения к базе данных"
    )
    
    # Supabase Configuration (optional)
    use_supabase: bool = Field(
        default=False,
        description="Использовать Supabase вместо SQLite"
    )
    supabase_url: Optional[str] = Field(
        default=None,
        description="URL Supabase проекта"
    )
    supabase_key: Optional[str] = Field(
        default=None,
        description="API ключ Supabase"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Уровень логирования"
    )
    
    # Optional: Future features
    redis_url: Optional[str] = Field(
        default=None,
        description="URL подключения к Redis (опционально)"
    )
    
    # Security
    max_file_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        description="Максимальный размер файла в байтах"
    )
    
    # Rate limiting (future)
    rate_limit_per_minute: int = Field(
        default=10,
        description="Лимит запросов в минуту на пользователя"
    )


# Глобальный экземпляр настроек
settings = Settings()
