#!/usr/bin/env python3
"""Тест системы оплаты."""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from src.payment_service import PaymentService
from loguru import logger


async def test_payment_system():
    """Тестирование системы оплаты."""
    logger.info("🧪 Начинаем тестирование системы оплаты")
    
    # Инициализируем базу данных
    from src.db_adapter import db_adapter
    await db_adapter.initialize()
    logger.info("База данных инициализирована")
    
    # Инициализируем сессии базы данных
    from src.db import init_db
    init_db()
    logger.info("Сессии базы данных инициализированы")
    
    # Тестовый пользователь
    test_user_id = 123456789
    
    try:
        # 1. Проверяем, что у пользователя нет подписки
        subscription = await PaymentService.get_user_subscription(test_user_id)
        logger.info(f"1. Подписка пользователя: {subscription}")
        
        # 2. Проверяем, может ли пользователь генерировать отчет
        can_generate = await PaymentService.can_user_generate_report(test_user_id)
        logger.info(f"2. Может генерировать отчет: {can_generate}")
        
        # 3. Создаем платеж на 1 отчет
        payment = await PaymentService.create_payment(test_user_id, "single")
        logger.info(f"3. Создан платеж: {payment}")
        
        # 4. Завершаем платеж
        success = await PaymentService.complete_payment(payment.id)
        logger.info(f"4. Платеж завершен: {success}")
        
        # 5. Проверяем подписку после оплаты
        subscription = await PaymentService.get_user_subscription(test_user_id)
        logger.info(f"5. Подписка после оплаты: {subscription}")
        
        # 6. Проверяем, может ли пользователь генерировать отчет
        can_generate = await PaymentService.can_user_generate_report(test_user_id)
        logger.info(f"6. Может генерировать отчет: {can_generate}")
        
        # 7. Используем отчет
        report_used = await PaymentService.use_user_report(test_user_id)
        logger.info(f"7. Отчет использован: {report_used}")
        
        # 8. Проверяем подписку после использования
        subscription = await PaymentService.get_user_subscription(test_user_id)
        logger.info(f"8. Подписка после использования: {subscription}")
        
        # 9. Создаем платеж на 100 отчетов
        bulk_payment = await PaymentService.create_payment(test_user_id, "bulk")
        logger.info(f"9. Создан оптовый платеж: {bulk_payment}")
        
        # 10. Завершаем оптовый платеж
        bulk_success = await PaymentService.complete_payment(bulk_payment.id)
        logger.info(f"10. Оптовый платеж завершен: {bulk_success}")
        
        # 11. Проверяем финальную подписку
        final_subscription = await PaymentService.get_user_subscription(test_user_id)
        logger.info(f"11. Финальная подписка: {final_subscription}")
        
        logger.info("✅ Тестирование системы оплаты завершено успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}", exc_info=True)
        raise


async def main():
    """Основная функция."""
    try:
        await test_payment_system()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
