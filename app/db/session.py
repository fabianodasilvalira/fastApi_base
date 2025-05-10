import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# Ajuste o caminho se necessário
load_dotenv(dotenv_path=".env")  # Use "/app/.env" se estiver rodando via Docker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não está configurada nas variáveis de ambiente.")

# Cria uma engine assíncrona do SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Cria uma fábrica de sessões assíncronas
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Função para obter uma sessão de banco de dados (usada como dependência no FastAPI)
@asynccontextmanager
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Comentários explicativos:
# - DATABASE_URL deve ser algo como: mysql+aiomysql://user:password@localhost:3306/dbname
# - echo=True imprime as queries no console, útil para debug.
# - future=True usa a API 2.0 do SQLAlchemy.
# - get_async_db é usado com Depends(get_async_db) em rotas para injetar uma sessão do banco.
