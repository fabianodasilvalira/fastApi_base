from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Criando um banco de dados SQLite em memória para testes
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Criando a engine e a sessão de testes
engine = create_async_engine(DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Função para criar uma nova sessão de banco de dados para os testes
async def get_test_db():
    async with TestingSessionLocal() as session:
        yield session
