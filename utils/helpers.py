"""General-purpose helper functions for formatting and text processing."""


def format_price(price: float) -> str:
    """Format price with space-separated thousands and so'm suffix.

    Examples:
        15000 -> '15 000 so'm'
        1500000 -> '1 500 000 so'm'
    """
    rounded = int(round(price))
    formatted = f"{rounded:,}".replace(",", " ")
    return f"{formatted} so'm"


def format_phone(phone: str) -> str:
    """Format phone number for display.

    Ensures the number starts with '+' and has proper spacing.
    Examples:
        '998901234567' -> '+998 90 123 45 67'
        '+998901234567' -> '+998 90 123 45 67'
    """
    # Strip any non-digit characters except leading +
    digits = phone.lstrip("+").replace(" ", "").replace("-", "")

    if len(digits) == 12 and digits.startswith("998"):
        return f"+{digits[:3]} {digits[3:5]} {digits[5:8]} {digits[8:10]} {digits[10:12]}"

    # Fallback: just prefix with + if not already present
    if not phone.startswith("+"):
        return f"+{phone}"
    return phone


def truncate_text(text: str, max_len: int = 50) -> str:
    """Truncate text to max_len characters, adding ellipsis if truncated.

    Examples:
        'Short text' -> 'Short text'
        'Very long text...' -> 'Very long te...'
    """
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_order_status(status: str) -> str:
    """Convert order status enum value to emoji + Uzbek text.

    Args:
        status: OrderStatus value string (e.g. 'NEW', 'ACCEPTED')

    Returns:
        Formatted status string with emoji
    """
    status_map = {
        "NEW": "🆕 Yangi",
        "ACCEPTED": "✅ Qabul qilindi",
        "DELIVERING": "🚚 Yetkazilmoqda",
        "COMPLETED": "✅ Bajarildi",
        "CANCELED": "❌ Bekor qilindi",
    }
    return status_map.get(status.upper(), f"❓ {status}")


def format_payment_type(ptype: str) -> str:
    """Convert payment type enum value to Uzbek text.

    Args:
        ptype: PaymentType value string (e.g. 'CASH', 'CLICK')

    Returns:
        Formatted payment type string
    """
    payment_map = {
        "CASH": "💵 Naqd pul",
        "CLICK": "📱 Click",
        "PAYME": "📱 Payme",
    }
    return payment_map.get(ptype.upper(), ptype)
