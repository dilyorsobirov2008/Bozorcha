from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.product import Product


class ProductService:
    """Service layer for Product CRUD and query operations."""

    @staticmethod
    async def get_by_category(
        session: AsyncSession,
        category_id: int,
        offset: int = 0,
        limit: int = 5,
    ) -> list[Product]:
        """Get products by category with pagination."""
        result = await session.execute(
            select(Product)
            .where(Product.category_id == category_id)
            .order_by(Product.id)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, product_id: int) -> Product | None:
        """Get a product by its id."""
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        category_id: int,
        name: str,
        price: int,
        image: str | None = None,
        stock: int = 0,
    ) -> Product:
        """Create a new product."""
        product = Product(
            category_id=category_id,
            name=name,
            price=price,
            image=image,
            stock=stock,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    @staticmethod
    async def update(
        session: AsyncSession, product_id: int, **kwargs
    ) -> Product | None:
        """Update a product with arbitrary fields. Returns None if not found."""
        product = await ProductService.get_by_id(session, product_id)
        if product is None:
            return None
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        await session.commit()
        await session.refresh(product)
        return product

    @staticmethod
    async def delete(session: AsyncSession, product_id: int) -> bool:
        """Delete a product by id. Returns True if deleted."""
        product = await ProductService.get_by_id(session, product_id)
        if product is None:
            return False
        await session.delete(product)
        await session.commit()
        return True

    @staticmethod
    async def search(
        session: AsyncSession,
        query: str,
        offset: int = 0,
        limit: int = 5,
    ) -> list[Product]:
        """Search products by name using case-insensitive LIKE."""
        result = await session.execute(
            select(Product)
            .where(Product.name.ilike(f"%{query}%"))
            .order_by(Product.id)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_by_category(session: AsyncSession, category_id: int) -> int:
        """Count products in a category."""
        result = await session.execute(
            select(func.count(Product.id)).where(
                Product.category_id == category_id
            )
        )
        return result.scalar_one()

    @staticmethod
    async def count_search(session: AsyncSession, query: str) -> int:
        """Count products matching a search query."""
        result = await session.execute(
            select(func.count(Product.id)).where(
                Product.name.ilike(f"%{query}%")
            )
        )
        return result.scalar_one()

    @staticmethod
    async def get_low_stock(
        session: AsyncSession, threshold: int = 5
    ) -> list[Product]:
        """Get products with stock at or below the given threshold."""
        result = await session.execute(
            select(Product)
            .where(Product.stock <= threshold)
            .order_by(Product.stock)
        )
        return list(result.scalars().all())
