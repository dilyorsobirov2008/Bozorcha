from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class CartItem(Base):
    """Shopping cart item model linking a user to a product with quantity."""

    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(default=1, server_default="1")

    # Relationships
    user = relationship("User", back_populates="cart_items", lazy="selectin")
    product = relationship("Product", back_populates="cart_items", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, qty={self.quantity})>"
