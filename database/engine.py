import re
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings

# Clean and format the DB_URL automatically to prevent driver/SSL errors
db_url = settings.DB_URL
if db_url and "postgresql" in db_url:
    # 1. Convert postgresql:// to postgresql+asyncpg:// if needed
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # 2. Replace sslmode with ssl=require (asyncpg uses ssl instead of sslmode)
    if "sslmode=" in db_url:
        db_url = re.sub(r'sslmode=[^&?]+', 'ssl=require', db_url)
    
    # 3. Remove channel_binding parameter (unsupported by asyncpg)
    db_url = re.sub(r'[&?]channel_binding=[^&?]+', '', db_url)
    
    # 4. Clean up any double query symbols (e.g. ?ssl=require& or similar if regex left orphans)
    db_url = db_url.replace("&&", "&").replace("?&", "?")

engine = create_async_engine(
    db_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
