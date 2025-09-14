"""Модели базы данных."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


class Ticket(Base):
    """Модель заявки на VIN отчет."""
    
    __tablename__ = "tickets"
    
    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Уникальный идентификатор заявки"
    )
    
    # VIN номер автомобиля
    vin: Mapped[str] = mapped_column(
        String(17),
        nullable=False,
        index=True,
        comment="VIN номер автомобиля (17 символов)"
    )
    
    # ID пользователя Telegram
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="ID пользователя Telegram"
    )
    
    # Статус заявки
    status: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Статус заявки: NEW, TAKEN, DONE"
    )
    
    # ID назначенного менеджера
    assignee_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
        comment="ID назначенного менеджера"
    )
    
    # Время создания заявки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Время создания заявки"
    )
    
    # Время обновления заявки
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="Время последнего обновления заявки"
    )
    
    def __repr__(self) -> str:
        """Строковое представление заявки."""
        return (
            f"<Ticket(id={self.id}, vin='{self.vin}', "
            f"user_id={self.user_id}, status='{self.status}', "
            f"assignee_id={self.assignee_id})>"
        )
    
    @property
    def is_new(self) -> bool:
        """Проверка, что заявка новая."""
        return self.status == "NEW"
    
    @property
    def is_taken(self) -> bool:
        """Проверка, что заявка назначена."""
        return self.status == "TAKEN"
    
    @property
    def is_done(self) -> bool:
        """Проверка, что заявка завершена."""
        return self.status == "DONE"
    
    def can_be_taken(self) -> bool:
        """Проверка, можно ли назначить заявку."""
        return self.status == "NEW"
    
    def can_be_done(self) -> bool:
        """Проверка, можно ли завершить заявку."""
        return self.status in ("NEW", "TAKEN")
