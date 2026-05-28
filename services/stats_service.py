from datetime import datetime, date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order
from models.order_item import OrderItem
from models.product import Product
from models.user import User


class StatsService:
    """Service layer for dashboard statistics."""

    @staticmethod
    async def today_orders_count(session: AsyncSession) -> int:
        """Count orders created today."""
        today = date.today()
        result = await session.execute(
            select(func.count(Order.id)).where(
                func.date(Order.created_at) == today
            )
        )
        return result.scalar_one()

    @staticmethod
    async def today_sales(session: AsyncSession) -> int:
        """Sum of totals for today's completed orders."""
        today = date.today()
        result = await session.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                func.date(Order.created_at) == today,
                Order.status == "completed",
            )
        )
        return result.scalar_one()

    @staticmethod
    async def monthly_sales(session: AsyncSession) -> int:
        """Sum of totals for this month's completed orders."""
        now = datetime.now()
        first_of_month = date(now.year, now.month, 1)
        result = await session.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                func.date(Order.created_at) >= first_of_month,
                Order.status == "completed",
            )
        )
        return result.scalar_one()

    @staticmethod
    async def users_count(session: AsyncSession) -> int:
        """Count total registered users."""
        result = await session.execute(select(func.count(User.id)))
        return result.scalar_one()

    @staticmethod
    async def top_product(session: AsyncSession) -> tuple[str, int] | None:
        """Get the most ordered product by total quantity in order_items.

        Returns a tuple of (product_name, total_quantity) or None if no orders.
        """
        result = await session.execute(
            select(
                Product.name,
                func.sum(OrderItem.quantity).label("total_qty"),
            )
            .join(Product, OrderItem.product_id == Product.id)
            .group_by(Product.id, Product.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(1)
        )
        row = result.first()
        if row is None:
            return None
        return (row[0], row[1])
