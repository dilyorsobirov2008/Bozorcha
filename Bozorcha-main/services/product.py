from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.product import Product


async def create_product(
    session: AsyncSession,
    name: str,
    description: str,
    price: float,
    stock: int,
    photo_id: str,
    category_id: int,
) -> Product:
    """Create a new product."""
    product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        photo_id=photo_id,
        category_id=category_id,
        is_active=True,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def get_products_by_category(
    session: AsyncSession,
    category_id: int,
    page: int = 0,
    per_page: int = 5,
) -> tuple[list[Product], int]:
    """Get paginated products for a category. Returns (products, total_count)."""
    # Total count
    count_stmt = select(func.count(Product.id)).where(
        Product.category_id == category_id, Product.is_active == True
    )
    count_result = await session.execute(count_stmt)
    total_count = count_result.scalar_one()

    # Paginated products
    stmt = (
        select(Product)
        .where(Product.category_id == category_id, Product.is_active == True)
        .order_by(Product.id)
        .offset(page * per_page)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    products = list(result.scalars().all())

    return products, total_count


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    """Get a single product by ID."""
    stmt = select(Product).where(Product.id == product_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_product(
    session: AsyncSession, product_id: int, **kwargs
) -> Product:
    """Update product fields."""
    stmt = select(Product).where(Product.id == product_id)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if product is None:
        raise ValueError(f"Product with id={product_id} not found")

    for key, value in kwargs.items():
        if hasattr(product, key):
            setattr(product, key, value)

    await session.commit()
    await session.refresh(product)
    return product


async def delete_product(session: AsyncSession, product_id: int) -> bool:
    """Soft delete a product by setting is_active to False."""
    stmt = select(Product).where(Product.id == product_id)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if product is None:
        return False

    product.is_active = False
    await session.commit()
    return True


async def search_products(
    session: AsyncSession,
    query: str,
    page: int = 0,
    per_page: int = 5,
) -> tuple[list[Product], int]:
    """Search products by name or description. Returns (products, total_count)."""
    search_pattern = f"%{query}%"

    filter_condition = or_(
        Product.name.ilike(search_pattern),
        Product.description.ilike(search_pattern),
    )

    # Total count
    count_stmt = select(func.count(Product.id)).where(
        filter_condition, Product.is_active == True
    )
    count_result = await session.execute(count_stmt)
    total_count = count_result.scalar_one()

    # Paginated results
    stmt = (
        select(Product)
        .where(filter_condition, Product.is_active == True)
        .order_by(Product.id)
        .offset(page * per_page)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    products = list(result.scalars().all())

    return products, total_count


async def get_low_stock_products(
    session: AsyncSession, threshold: int = 5
) -> list[Product]:
    """Get products with stock at or below the given threshold."""
    stmt = (
        select(Product)
        .where(Product.is_active == True, Product.stock <= threshold)
        .order_by(Product.stock)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_products(
    session: AsyncSession, category_id: int | None = None
) -> int:
    """Count active products, optionally filtered by category."""
    stmt = select(func.count(Product.id)).where(Product.is_active == True)

    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)

    result = await session.execute(stmt)
    return result.scalar_one()
