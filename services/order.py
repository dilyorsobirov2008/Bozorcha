from datetime import datetime, date

from sqlalchemy import select, func, delete, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.order import Order, OrderItem, OrderStatus, PaymentType
from models.cart import CartItem
from models.product import Product


async def create_order_from_cart(
    session: AsyncSession,
    user_id: int,
    phone: str,
    address: str,
    payment_type: PaymentType,
) -> Order | None:
    """Create an order from the user's cart items.

    - Creates Order and OrderItem records
    - Decrements product stock
    - Clears the cart
    Returns None if cart is empty.
    """
    # Get cart items with products
    cart_stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.product))
    )
    cart_result = await session.execute(cart_stmt)
    cart_items = list(cart_result.scalars().all())

    if not cart_items:
        return None

    # Calculate total
    total = sum(item.quantity * item.product.price for item in cart_items)

    # Create order
    order = Order(
        user_id=user_id,
        phone=phone,
        address=address,
        payment_type=payment_type,
        status=OrderStatus.NEW,
        total=total,
        created_at=datetime.utcnow(),
    )
    session.add(order)
    await session.flush()  # Get order.id

    # Create order items and decrement stock
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=cart_item.product.price,
        )
        session.add(order_item)

        # Decrement stock
        product_stmt = select(Product).where(Product.id == cart_item.product_id)
        product_result = await session.execute(product_stmt)
        product = product_result.scalar_one()
        product.stock = max(0, product.stock - cart_item.quantity)

    # Clear cart
    clear_stmt = delete(CartItem).where(CartItem.user_id == user_id)
    await session.execute(clear_stmt)

    await session.commit()
    await session.refresh(order)
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    """Get order by ID with items loaded."""
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_orders(session: AsyncSession, user_id: int) -> list[Order]:
    """Get all orders for a user, newest first."""
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_order_status(
    session: AsyncSession, order_id: int, status: OrderStatus
) -> Order:
    """Update the status of an order."""
    stmt = select(Order).where(Order.id == order_id)
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()

    if order is None:
        raise ValueError(f"Order with id={order_id} not found")

    order.status = status
    await session.commit()
    await session.refresh(order)
    return order


async def get_today_orders(session: AsyncSession) -> list[Order]:
    """Get all orders created today."""
    today = date.today()
    stmt = (
        select(Order)
        .where(func.date(Order.created_at) == today)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_today_stats(session: AsyncSession) -> dict:
    """Get today's order statistics: count and total sum."""
    today = date.today()
    stmt = select(
        func.count(Order.id).label("count"),
        func.coalesce(func.sum(Order.total), 0).label("total_sum"),
    ).where(func.date(Order.created_at) == today)

    result = await session.execute(stmt)
    row = result.one()
    return {"count": row.count, "total_sum": float(row.total_sum)}


async def get_monthly_stats(session: AsyncSession) -> dict:
    """Get current month's order statistics."""
    now = datetime.utcnow()
    stmt = select(
        func.count(Order.id).label("count"),
        func.coalesce(func.sum(Order.total), 0).label("total_sum"),
    ).where(
        extract("year", Order.created_at) == now.year,
        extract("month", Order.created_at) == now.month,
    )

    result = await session.execute(stmt)
    row = result.one()
    return {"count": row.count, "total_sum": float(row.total_sum)}


async def get_total_sales(session: AsyncSession) -> dict:
    """Get all-time order statistics."""
    stmt = select(
        func.count(Order.id).label("count"),
        func.coalesce(func.sum(Order.total), 0).label("total_sum"),
    )

    result = await session.execute(stmt)
    row = result.one()
    return {"count": row.count, "total_sum": float(row.total_sum)}


async def get_best_selling(
    session: AsyncSession, limit: int = 5
) -> list[dict]:
    """Get best-selling products by total quantity ordered."""
    stmt = (
        select(
            Product.name.label("product_name"),
            func.sum(OrderItem.quantity).label("total_qty"),
        )
        .join(Product, OrderItem.product_id == Product.id)
        .group_by(Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()
    return [
        {"product_name": row.product_name, "total_qty": int(row.total_qty)}
        for row in rows
    ]
