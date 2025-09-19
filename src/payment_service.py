"""Сервис для работы с платежами и подписками."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db_session
from .models import Payment, UserSubscription


class PaymentService:
    """Сервис для управления платежами и подписками."""
    
    # Тарифы
    SINGLE_REPORT_PRICE = 200  # $2.00 в центах
    BULK_REPORTS_PRICE = 10000  # $100.00 в центах
    BULK_REPORTS_COUNT = 100
    
    @staticmethod
    async def get_user_subscription(user_id: int) -> Optional[UserSubscription]:
        """Получить подписку пользователя."""
        async with get_db_session() as session:
            result = session.execute(
                select(UserSubscription).where(UserSubscription.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user_subscription(user_id: int, reports_count: int) -> UserSubscription:
        """Создать или обновить подписку пользователя."""
        async with get_db_session() as session:
            # Проверяем, есть ли уже подписка
            existing = session.execute(
                select(UserSubscription).where(UserSubscription.user_id == user_id)
            )
            subscription = existing.scalar_one_or_none()
            
            if subscription:
                # Обновляем существующую подписку
                subscription.reports_remaining += reports_count
                subscription.total_reports += reports_count
                subscription.updated_at = datetime.utcnow()
            else:
                # Создаем новую подписку
                subscription = UserSubscription(
                    user_id=user_id,
                    reports_remaining=reports_count,
                    total_reports=reports_count
                )
                session.add(subscription)
            
            session.commit()
            session.refresh(subscription)
            
            logger.info(
                "Подписка пользователя обновлена",
                user_id=user_id,
                reports_added=reports_count,
                total_remaining=subscription.reports_remaining
            )
            
            return subscription
    
    @staticmethod
    async def can_user_generate_report(user_id: int) -> bool:
        """Проверить, может ли пользователь сгенерировать отчет."""
        subscription = await PaymentService.get_user_subscription(user_id)
        return subscription is not None and subscription.can_generate_report()
    
    @staticmethod
    async def use_user_report(user_id: int) -> bool:
        """Использовать один отчет пользователя."""
        async with get_db_session() as session:
            result = session.execute(
                select(UserSubscription).where(UserSubscription.user_id == user_id)
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                logger.warning("Попытка использовать отчет без подписки", user_id=user_id)
                return False
            
            if subscription.use_report():
                session.commit()
                logger.info(
                    "Отчет использован",
                    user_id=user_id,
                    reports_remaining=subscription.reports_remaining
                )
                return True
            else:
                logger.warning("Недостаточно отчетов для использования", user_id=user_id)
                return False
    
    @staticmethod
    async def create_payment(
        user_id: int,
        payment_type: str,
        payment_provider: str = "manual"
    ) -> Payment:
        """Создать платеж."""
        if payment_type == "single":
            amount = PaymentService.SINGLE_REPORT_PRICE
            reports_count = 1
        elif payment_type == "bulk":
            amount = PaymentService.BULK_REPORTS_PRICE
            reports_count = PaymentService.BULK_REPORTS_COUNT
        else:
            raise ValueError(f"Неизвестный тип платежа: {payment_type}")
        
        async with get_db_session() as session:
            payment = Payment(
                user_id=user_id,
                amount=amount,
                currency="USD",
                payment_type=payment_type,
                reports_count=reports_count,
                status="pending",
                payment_provider=payment_provider
            )
            
            session.add(payment)
            session.commit()
            session.refresh(payment)
            
            logger.info(
                "Создан платеж",
                payment_id=payment.id,
                user_id=user_id,
                payment_type=payment_type,
                amount=amount
            )
            
            return payment
    
    @staticmethod
    async def complete_payment(payment_id: int) -> bool:
        """Завершить платеж."""
        async with get_db_session() as session:
            result = session.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            payment = result.scalar_one_or_none()
            
            if not payment:
                logger.error("Платеж не найден", payment_id=payment_id)
                return False
            
            if payment.status != "pending":
                logger.warning("Платеж уже обработан", payment_id=payment_id, status=payment.status)
                return False
            
            # Обновляем статус платежа
            payment.status = "completed"
            payment.completed_at = datetime.utcnow()
            
            # Добавляем отчеты в подписку пользователя
            await PaymentService.create_user_subscription(
                payment.user_id,
                payment.reports_count
            )
            
            session.commit()
            
            logger.info(
                "Платеж завершен",
                payment_id=payment_id,
                user_id=payment.user_id,
                reports_added=payment.reports_count
            )
            
            return True
    
    @staticmethod
    async def get_payment_info(payment_id: int) -> Optional[Payment]:
        """Получить информацию о платеже."""
        async with get_db_session() as session:
            result = session.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    def format_price(amount_cents: int) -> str:
        """Форматировать цену для отображения."""
        return f"${amount_cents / 100:.2f}"
    
    @staticmethod
    def get_payment_description(payment_type: str) -> str:
        """Получить описание платежа."""
        if payment_type == "single":
            return f"1 отчет за {PaymentService.format_price(PaymentService.SINGLE_REPORT_PRICE)}"
        elif payment_type == "bulk":
            return f"100 отчетов за {PaymentService.format_price(PaymentService.BULK_REPORTS_PRICE)}"
        else:
            return "Неизвестный тариф"
