from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.settings import Setting


async def get_setting(session: AsyncSession, key: str) -> str | None:
    """Get a setting value by key."""
    stmt = select(Setting).where(Setting.key == key)
    result = await session.execute(stmt)
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def set_setting(session: AsyncSession, key: str, value: str) -> Setting:
    """Set a setting value. Creates or updates."""
    stmt = select(Setting).where(Setting.key == key)
    result = await session.execute(stmt)
    setting = result.scalar_one_or_none()

    if setting is None:
        setting = Setting(key=key, value=value)
        session.add(setting)
    else:
        setting.value = value

    await session.commit()
    await session.refresh(setting)
    return setting


async def get_delivery_price(session: AsyncSession) -> float:
    """Get delivery price from settings, default 15000."""
    value = await get_setting(session, "delivery_price")
    if value is None:
        return 15000.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 15000.0


async def set_delivery_price(session: AsyncSession, price: float) -> None:
    """Set the delivery price."""
    await set_setting(session, "delivery_price", str(price))


async def get_payment_toggles(session: AsyncSession) -> dict:
    """Get payment method toggles. Returns dict with cash, click, payme keys."""
    toggles = {
        "cash": True,
        "click": True,
        "payme": True,
    }

    for payment_type in toggles:
        value = await get_setting(session, f"payment_{payment_type}")
        if value is not None:
            toggles[payment_type] = value.lower() in ("true", "1", "yes", "on")

    return toggles


async def set_payment_toggle(
    session: AsyncSession, payment_type: str, enabled: bool
) -> None:
    """Enable or disable a payment type."""
    await set_setting(session, f"payment_{payment_type}", str(enabled).lower())
