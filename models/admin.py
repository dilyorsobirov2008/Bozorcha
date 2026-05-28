from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Admin(Base):
    """Admin user model with hashed password authentication."""

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<Admin(id={self.id}, login={self.login!r})>"
