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

