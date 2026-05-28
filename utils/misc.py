def format_price(price: int) -> str:
    """Format price with space separators, e.g. 12000 -> 12 000 so'm."""
    return f"{price:,}".replace(",", " ")
