from sqlalchemy.ext.asyncio import create_async_engine

from src.config import settings

engine = create_async_engine(settings.POSTGRES_CONNECTION_STRING)
