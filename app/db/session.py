# app/db/session.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# Ajuste o caminho se o .env estiver em um local diferente em relação a este arquivo
# No contexto do Docker, o .env estará na raiz do /app
load_dotenv(dotenv_path="/app/.env") 

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não está configurada nas variáveis de ambiente.")

# Cria uma engine assíncrona do SQLAlchemy
# Para MySQL com aiomysql: "mysql+aiomysql://user:password@host/dbname"
# Para PostgreSQL com asyncpg: "postgresql+asyncpg://user:password@host/dbname"
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Cria uma fábrica de sessões assíncronas
# expire_on_commit=False evita que os atributos dos objetos expirem após o commit,
# o que é útil se você precisar acessar os dados após o commit sem recarregar do DB.
AsyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Função para obter uma sessão de banco de dados (usada como dependência no FastAPI)
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Se você precisar de uma sessão síncrona para Alembic ou scripts, pode definir aqui também
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# SQLALCHEMY_DATABASE_URL_SYNC = DATABASE_URL.replace("+aiomysql", "") # Exemplo para converter para sync
# engine_sync = create_engine(SQLALCHEMY_DATABASE_URL_SYNC)
# SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine_sync)

# Comentários em português:
# - `DATABASE_URL`: URL de conexão com o banco de dados, lida do arquivo .env.
# - `engine`: Engine assíncrona do SQLAlchemy, configurada com a `DATABASE_URL`.
#   `echo=True` é útil para debugging, pois loga as queries SQL executadas.
#   `future=True` habilita o estilo de API 2.0 do SQLAlchemy.
# - `AsyncSessionLocal`: Fábrica para criar sessões de banco de dados assíncronas (`AsyncSession`).
# - `get_async_db`: Função geradora assíncrona que será usada como dependência do FastAPI
#   para injetar uma `AsyncSession` nas rotas. Garante que a sessão seja fechada após a requisição.
# - A seção comentada mostra como você poderia configurar uma engine e sessão síncronas se necessário
#   (por exemplo, para uso com Alembic se ele não estiver configurado para async, ou para scripts de manutenção).
# - É crucial que a `DATABASE_URL` no seu arquivo `.env` seja compatível com um driver assíncrono
#   (ex: `mysql+aiomysql://...` para MySQL, `postgresql+asyncpg://...` para PostgreSQL).

