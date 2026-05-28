class Paginator:
    def __init__(self, total: int, per_page: int, current_page: int):
        self.total = total
        self.per_page = per_page
        self.current_page = current_page

    @property
    def total_pages(self) -> int:
        if self.total <= 0:
            return 1
        return (self.total + self.per_page - 1) // self.per_page

    @property
    def has_prev(self) -> bool:
        return self.current_page > 1

    @property
    def has_next(self) -> bool:
        return self.current_page < self.total_pages

    @property
    def offset(self) -> int:
        return (self.current_page - 1) * self.per_page
