from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/supermarket_bot"
    ADMIN_IDS: list[int] = []
    ADMIN_GROUP_ID: int = 0

    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8'}

    def __init__(self, **values):
        super().__init__(**values)
        # Automatically convert standard Postgres URL prefixes to async pg driver format
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.DATABASE_URL.startswith("postgresql://") and not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

settings = Settings()
