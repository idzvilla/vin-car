from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Ticket(Base):
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Уникальный идентификатор заявки"
    )
    
    vin: Mapped[str] = mapped_column(
        String(17),
        nullable=False,
        index=True,
        comment="VIN номер автомобиля (17 символов)"
    )
    
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="ID пользователя Telegram"
    )
    
    status: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Статус заявки: NEW, TAKEN, DONE"
    )
    
    assignee_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="ID назначенного менеджера"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Время создания заявки"
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="Время последнего обновления заявки"
    )
    
    def __repr__(self) -> str:
        return (
            f"<Ticket(id={self.id}, vin='{self.vin}', "
            f"user_id={self.user_id}, status='{self.status}', "
            f"assignee_id={self.assignee_id})>"
        )
    
    @property
    def is_new(self) -> bool:
        return self.status == "NEW"
    
    @property
    def is_taken(self) -> bool:
        return self.status == "TAKEN"
    
    @property
    def is_done(self) -> bool:
        return self.status == "DONE"
    
    def can_be_taken(self) -> bool:
        return self.status == "NEW"
    
    def can_be_done(self) -> bool:
        return self.status in ("NEW", "TAKEN")


class Payment(Base):
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Уникальный идентификатор платежа"
    )
    
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="ID пользователя Telegram"
    )
    
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Сумма платежа в центах"
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        comment="Валюта платежа"
    )
    
    payment_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Тип платежа: single, bulk"
    )
    
    reports_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Количество отчетов в платеже"
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="Статус платежа: pending, completed, failed"
    )
    
    payment_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Провайдер платежа: stripe, paypal, etc"
    )
    
    external_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Внешний ID платежа от провайдера"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Время создания платежа"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время завершения платежа"
    )
    
    def __repr__(self) -> str:
        return (
            f"<Payment(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, type='{self.payment_type}', "
            f"status='{self.status}')>"
        )


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Уникальный идентификатор подписки"
    )
    
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="ID пользователя Telegram"
    )
    
    reports_remaining: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Количество оставшихся отчетов"
    )
    
    total_reports: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Общее количество купленных отчетов"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Время создания подписки"
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="Время последнего обновления подписки"
    )
    
    def __repr__(self) -> str:
        return (
            f"<UserSubscription(user_id={self.user_id}, "
            f"reports_remaining={self.reports_remaining}, "
            f"total_reports={self.total_reports})>"
        )
    
    def can_generate_report(self) -> bool:
        return self.reports_remaining > 0
    
    def use_report(self) -> bool:
        if self.reports_remaining > 0:
            self.reports_remaining -= 1
            return True
        return False

