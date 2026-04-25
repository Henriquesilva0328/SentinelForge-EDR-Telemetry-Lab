from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sentinelforge.core.settings import get_settings

# Mantemos engine e session factory como singletons lazy.
# Isso evita efeitos colaterais pesados no import do módulo,
# o que ajuda muito em testes e em ambientes de CI.
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Retorna a engine assíncrona da aplicação.

    A engine é criada sob demanda na primeira chamada,
    em vez de ser criada no import do módulo.
    """
    global _engine

    if _engine is None:
        settings = get_settings()

        _engine = create_async_engine(
            settings.db_url,
            pool_pre_ping=True,
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Retorna a factory de sessões assíncronas.

    Também é criada de forma lazy para evitar acoplamento
    de import com infraestrutura.
    """
    global _session_factory

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _session_factory


# Mantemos esse alias para compatibilidade com o restante do projeto.
SessionFactory = get_session_factory()


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    Dependency do FastAPI para fornecer sessão de banco.
    """
    async with get_session_factory()() as session:
        yield session