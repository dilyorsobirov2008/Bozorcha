from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    BOT_TOKEN: str
    DB_URL: str
    ADMIN_GROUP_ID: int = 0
    DELIVERY_PRICE: int = 10000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
