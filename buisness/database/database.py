from dotenv import load_dotenv
import os
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Read raw DATABASE_URL (may contain ${VAR} placeholders) and expand them.
raw_db_url = os.getenv("DATABASE_URL")
if not raw_db_url:
    raise RuntimeError("DATABASE_URL environment variable is not set")

# Expand any ${VAR} occurrences using environment variables from .env
DATABASE_URL = os.path.expandvars(raw_db_url)

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with SessionLocal() as session:
        yield session
