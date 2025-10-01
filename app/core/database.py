from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Criar engine assíncrono
engine = create_async_engine(settings.database_url, echo=False)

# Criar fábrica de sessão assíncrona
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependência para obter sessão do banco de dados"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()



