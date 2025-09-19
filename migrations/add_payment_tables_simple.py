#!/usr/bin/env python3
"""Простая миграция для добавления таблиц платежей и подписок."""

import sqlite3
from pathlib import Path
from loguru import logger


def create_payment_tables():
    """Создать таблицы для платежей и подписок в SQLite."""
    db_path = Path(__file__).parent.parent / "vin_reports.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Создаем таблицу платежей
        cursor.execute("""
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
        
        # Создаем таблицу подписок
        cursor.execute("""
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id)")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Таблицы платежей и подписок созданы успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц: {e}")
        raise


def main():
    """Основная функция миграции."""
    logger.info("🚀 Начинаем миграцию: добавление таблиц платежей")
    
    try:
        create_payment_tables()
        logger.info("✅ Миграция завершена успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
