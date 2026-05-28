from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Product(Base):
    """Product model linked to a category."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    stock: Mapped[int] = mapped_column(default=0, server_default="0")

    # Relationships
    category = relationship("Category", back_populates="products", lazy="selectin")
    cart_items = relationship("CartItem", back_populates="product", lazy="selectin")
    order_items = relationship("OrderItem", back_populates="product", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name!r}, price={self.price})>"
