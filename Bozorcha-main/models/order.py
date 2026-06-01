import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Numeric, Integer, ForeignKey, DateTime, Enum, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.user import User
    from models.product import Product


class OrderStatus(str, enum.Enum):
    NEW = 'new'
    ACCEPTED = 'accepted'
    DELIVERING = 'delivering'
    COMPLETED = 'completed'
    CANCELED = 'canceled'


class PaymentType(str, enum.Enum):
    CASH = 'cash'
    CLICK = 'click'
    PAYME = 'payme'


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.NEW
    )
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    phone: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(Text)
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user: Mapped['User'] = relationship('User', lazy='selectin')
    items: Mapped[List['OrderItem']] = relationship(
        'OrderItem', back_populates='order', lazy='selectin'
    )


class OrderItem(Base):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    order: Mapped['Order'] = relationship('Order', back_populates='items')
    product: Mapped['Product'] = relationship('Product', lazy='selectin')
