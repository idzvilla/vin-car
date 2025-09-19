#!/usr/bin/env python3
"""Простой тест системы оплаты без async/await."""

import sqlite3
from pathlib import Path
from loguru import logger


def test_payment_system():
    """Тестирование системы оплаты."""
    logger.info("🧪 Начинаем тестирование системы оплаты")
    
    db_path = Path(__file__).parent / "vin_reports.db"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Тестовый пользователь
        test_user_id = 123456789
        
        # 1. Проверяем, что у пользователя нет подписки
        cursor.execute("SELECT * FROM user_subscriptions WHERE user_id = ?", (test_user_id,))
        subscription = cursor.fetchone()
        logger.info(f"1. Подписка пользователя: {subscription}")
        
        # 2. Создаем платеж на 1 отчет
        cursor.execute("""
            INSERT INTO payments (user_id, amount, currency, payment_type, reports_count, status, payment_provider)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (test_user_id, 200, "USD", "single", 1, "pending", "manual"))
        
        payment_id = cursor.lastrowid
        logger.info(f"2. Создан платеж: ID={payment_id}")
        
        # 3. Завершаем платеж
        cursor.execute("""
            UPDATE payments 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (payment_id,))
        
        # 4. Создаем подписку
        cursor.execute("""
            INSERT OR REPLACE INTO user_subscriptions (user_id, reports_remaining, total_reports)
            VALUES (?, COALESCE((SELECT reports_remaining FROM user_subscriptions WHERE user_id = ?), 0) + ?, 
                   COALESCE((SELECT total_reports FROM user_subscriptions WHERE user_id = ?), 0) + ?)
        """, (test_user_id, test_user_id, 1, test_user_id, 1))
        
        conn.commit()
        logger.info("3. Платеж завершен, подписка создана")
        
        # 5. Проверяем подписку
        cursor.execute("SELECT * FROM user_subscriptions WHERE user_id = ?", (test_user_id,))
        subscription = cursor.fetchone()
        logger.info(f"4. Подписка после оплаты: {subscription}")
        
        # 6. Используем отчет
        cursor.execute("""
            UPDATE user_subscriptions 
            SET reports_remaining = reports_remaining - 1
            WHERE user_id = ? AND reports_remaining > 0
        """, (test_user_id,))
        
        conn.commit()
        logger.info("5. Отчет использован")
        
        # 7. Проверяем подписку после использования
        cursor.execute("SELECT * FROM user_subscriptions WHERE user_id = ?", (test_user_id,))
        subscription = cursor.fetchone()
        logger.info(f"6. Подписка после использования: {subscription}")
        
        # 8. Создаем оптовый платеж
        cursor.execute("""
            INSERT INTO payments (user_id, amount, currency, payment_type, reports_count, status, payment_provider)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (test_user_id, 10000, "USD", "bulk", 100, "pending", "manual"))
        
        bulk_payment_id = cursor.lastrowid
        logger.info(f"7. Создан оптовый платеж: ID={bulk_payment_id}")
        
        # 9. Завершаем оптовый платеж
        cursor.execute("""
            UPDATE payments 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (bulk_payment_id,))
        
        # 10. Обновляем подписку
        cursor.execute("""
            UPDATE user_subscriptions 
            SET reports_remaining = reports_remaining + 100, total_reports = total_reports + 100
            WHERE user_id = ?
        """, (test_user_id,))
        
        conn.commit()
        logger.info("8. Оптовый платеж завершен, подписка обновлена")
        
        # 11. Проверяем финальную подписку
        cursor.execute("SELECT * FROM user_subscriptions WHERE user_id = ?", (test_user_id,))
        final_subscription = cursor.fetchone()
        logger.info(f"9. Финальная подписка: {final_subscription}")
        
        # 12. Проверяем все платежи
        cursor.execute("SELECT * FROM payments WHERE user_id = ?", (test_user_id,))
        payments = cursor.fetchall()
        logger.info(f"10. Все платежи пользователя: {payments}")
        
        conn.close()
        
        logger.info("✅ Тестирование системы оплаты завершено успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}", exc_info=True)
        raise


def main():
    """Основная функция."""
    try:
        test_payment_system()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
