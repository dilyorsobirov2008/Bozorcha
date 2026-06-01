import math
from typing import Any


class Paginator:
    """Generic paginator for splitting items across pages."""

    def __init__(self, items: list[Any], page: int = 0, per_page: int = 8):
        self._items = items
        self._page = page
        self._per_page = per_page

    @property
    def current_page(self) -> int:
        """Current page index (0-based)."""
        return self._page

    @property
    def total_pages(self) -> int:
        """Total number of pages."""
        if not self._items:
            return 1
        return math.ceil(len(self._items) / self._per_page)

    @property
    def has_prev(self) -> bool:
        """Whether there is a previous page."""
        return self._page > 0

    @property
    def has_next(self) -> bool:
        """Whether there is a next page."""
        return self._page < self.total_pages - 1

    @property
    def get_page_items(self) -> list[Any]:
        """Get items for the current page."""
        start = self._page * self._per_page
        end = start + self._per_page
        return self._items[start:end]


def format_price(price: float) -> str:
    """Format price with space-separated thousands and so'm suffix.

    Examples:
        15000 -> '15 000 so'm'
        1500000 -> '1 500 000 so'm'
        99.5 -> '100 so'm'
    """
    rounded = int(round(price))
    formatted = f"{rounded:,}".replace(",", " ")
    return f"{formatted} so'm"
