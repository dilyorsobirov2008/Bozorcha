from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.cart import CartItem
from models.product import Product


class CartService:
    """Service layer for shopping cart operations."""

    @staticmethod
    async def add_item(
        session: AsyncSession,
        user_id: int,
        product_id: int,
        quantity: int = 1,
    ) -> CartItem:
        """Add an item to the cart. If it already exists, increment quantity."""
        result = await session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )
        item = result.scalar_one_or_none()

        if item is not None:
            item.quantity += quantity
            await session.commit()
            await session.refresh(item)
            return item

        item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def get_items(session: AsyncSession, user_id: int) -> list[CartItem]:
        """Get all cart items for a user with eagerly loaded product."""
        result = await session.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
            .order_by(CartItem.id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_quantity(
        session: AsyncSession, cart_item_id: int, quantity: int
    ) -> CartItem | None:
        """Update item quantity. Deletes item if quantity <= 0."""
        result = await session.execute(
            select(CartItem).where(CartItem.id == cart_item_id)
        )
        item = result.scalar_one_or_none()
        if item is None:
            return None

        if quantity <= 0:
            await session.delete(item)
            await session.commit()
            return None

        item.quantity = quantity
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def remove_item(session: AsyncSession, cart_item_id: int) -> bool:
        """Remove a single cart item by id."""
        result = await session.execute(
            select(CartItem).where(CartItem.id == cart_item_id)
        )
        item = result.scalar_one_or_none()
        if item is None:
            return False
        await session.delete(item)
        await session.commit()
        return True

    @staticmethod
    async def clear(session: AsyncSession, user_id: int) -> None:
        """Remove all cart items for a user."""
        await session.execute(
            delete(CartItem).where(CartItem.user_id == user_id)
        )
        await session.commit()

    @staticmethod
    async def get_total(session: AsyncSession, user_id: int) -> int:
        """Calculate the total price of all items in a user's cart."""
        result = await session.execute(
            select(func.coalesce(func.sum(Product.price * CartItem.quantity), 0))
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.user_id == user_id)
        )
        return result.scalar_one()
