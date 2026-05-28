from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from models.cart import CartItem
from models.order import Order, OrderItem
from models.product import Product
from models.user import User


class OrderService:
    """Service layer for Order operations."""

    @staticmethod
    async def create_from_cart(
        session: AsyncSession,
        user_id: int,
        address: str,
        phone: str,
        payment_type: str,
    ) -> Order | None:
        """Create an order from the user's cart items.

        Moves cart items to order_items, calculates total,
        clears the cart, and decrements product stock.
        Returns None if the cart is empty.
        """
        # Fetch cart items with products
        cart_result = await session.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
        )
        cart_items = list(cart_result.scalars().all())

        if not cart_items:
            return None

        # Calculate total
        total = sum(item.product.price * item.quantity for item in cart_items)

        # Create order
        order = Order(
            user_id=user_id,
            total=total,
            address=address,
            phone=phone,
            payment_type=payment_type,
        )
        session.add(order)
        await session.flush()  # Get the order.id

        # Create order items and update stock
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
            )
            session.add(order_item)

            # Decrement product stock
            cart_item.product.stock = max(
                0, cart_item.product.stock - cart_item.quantity
            )

        # Clear cart
        await session.execute(
            delete(CartItem).where(CartItem.user_id == user_id)
        )

        await session.commit()
        await session.refresh(order)
        return order

    @staticmethod
    async def get_by_status(
        session: AsyncSession,
        status: str,
        offset: int = 0,
        limit: int = 5,
    ) -> list[Order]:
        """Get orders by status with joined user, paginated."""
        result = await session.execute(
            select(Order)
            .where(Order.status == status)
            .options(joinedload(Order.user))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.unique().scalars().all())

    @staticmethod
    async def count_by_status(session: AsyncSession, status: str) -> int:
        """Count orders with a given status."""
        result = await session.execute(
            select(func.count(Order.id)).where(Order.status == status)
        )
        return result.scalar_one()

    @staticmethod
    async def update_status(
        session: AsyncSession, order_id: int, status: str
    ) -> Order | None:
        """Update the status of an order."""
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if order is None:
            return None
        order.status = status
        await session.commit()
        await session.refresh(order)
        return order

    @staticmethod
    async def get_by_id(session: AsyncSession, order_id: int) -> Order | None:
        """Get an order by id with joined items and their products."""
        result = await session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                joinedload(Order.user),
            )
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_user_orders(
        session: AsyncSession, user_id: int
    ) -> list[Order]:
        """Get all orders for a user, newest first."""
        result = await session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())
