#!/usr/bin/env python3
"""Миграция для добавления таблиц платежей и подписок."""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_db_session
from src.models import Base, Payment, UserSubscription
from loguru import logger


async def create_payment_tables():
    """Создать таблицы для платежей и подписок."""
    try:
        async with get_db_session() as session:
            # Создаем таблицы
            await session.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT NOT NULL,
                    amount INTEGER NOT NULL,
                    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
                    payment_type VARCHAR(20) NOT NULL,
                    reports_count INTEGER NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    payment_provider VARCHAR(50) NOT NULL,
                    external_id VARCHAR(100),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME
                )
            """)
            
            await session.execute("""
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT NOT NULL,
                    reports_remaining INTEGER NOT NULL DEFAULT 0,
                    total_reports INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
            """)
            
            # Создаем индексы
            await session.execute("CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)")
            await session.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)")
            await session.execute("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id)")
            
            await session.commit()
            
            logger.info("✅ Таблицы платежей и подписок созданы успешно")
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц: {e}")
        raise


async def main():
    """Основная функция миграции."""
    logger.info("🚀 Начинаем миграцию: добавление таблиц платежей")
    
    try:
        await create_payment_tables()
        logger.info("✅ Миграция завершена успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
