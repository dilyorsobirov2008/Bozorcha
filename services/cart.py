from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.cart import CartItem
from models.product import Product


async def add_to_cart(
    session: AsyncSession,
    user_id: int,
    product_id: int,
    quantity: int = 1,
) -> CartItem:
    """Add item to cart. If already exists, increment quantity."""
    stmt = select(CartItem).where(
        CartItem.user_id == user_id, CartItem.product_id == product_id
    )
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if item is not None:
        item.quantity += quantity
    else:
        item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )
        session.add(item)

    await session.commit()
    await session.refresh(item)
    return item


async def get_cart(session: AsyncSession, user_id: int) -> list[CartItem]:
    """Get all cart items for a user with product relationships loaded."""
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.product))
        .order_by(CartItem.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_cart_item(session: AsyncSession, item_id: int) -> CartItem | None:
    """Get a single cart item by ID."""
    stmt = (
        select(CartItem)
        .where(CartItem.id == item_id)
        .options(selectinload(CartItem.product))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_cart_quantity(
    session: AsyncSession, item_id: int, quantity: int
) -> CartItem | None:
    """Update cart item quantity. Deletes the item if quantity <= 0."""
    stmt = select(CartItem).where(CartItem.id == item_id)
    result = await session.execute(stmt)
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


async def remove_from_cart(session: AsyncSession, item_id: int) -> bool:
    """Remove a specific item from the cart."""
    stmt = select(CartItem).where(CartItem.id == item_id)
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if item is None:
        return False

    await session.delete(item)
    await session.commit()
    return True


async def clear_cart(session: AsyncSession, user_id: int) -> None:
    """Remove all items from user's cart."""
    stmt = delete(CartItem).where(CartItem.user_id == user_id)
    await session.execute(stmt)
    await session.commit()


async def get_cart_total(
    session: AsyncSession, user_id: int
) -> tuple[int, float]:
    """Calculate cart totals. Returns (item_count, total_price)."""
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.product))
    )
    result = await session.execute(stmt)
    items = list(result.scalars().all())

    item_count = sum(item.quantity for item in items)
    total_price = sum(item.quantity * item.product.price for item in items)

    return item_count, total_price
