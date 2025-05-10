import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from typing import AsyncGenerator # Importar AsyncGenerator

# Carrega as variáveis de ambiente do arquivo .env
# Ajuste o caminho se necessário
# Prioriza o .env na raiz do projeto, depois na pasta app, depois o /app/.env (Docker)
DOTENV_PATH_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
DOTENV_PATH_APP_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
DOTENV_PATH_DOCKER = "/app/.env"

ACTUAL_DOTENV_PATH = None
if os.path.exists(DOTENV_PATH_PROJECT_ROOT):
    ACTUAL_DOTENV_PATH = DOTENV_PATH_PROJECT_ROOT
elif os.path.exists(DOTENV_PATH_APP_ROOT):
    ACTUAL_DOTENV_PATH = DOTENV_PATH_APP_ROOT
elif os.path.exists(DOTENV_PATH_DOCKER):
    ACTUAL_DOTENV_PATH = DOTENV_PATH_DOCKER

if ACTUAL_DOTENV_PATH:
    # print(f"Carregando .env de: {ACTUAL_DOTENV_PATH}") # Removido para não poluir logs do uvicorn
    load_dotenv(ACTUAL_DOTENV_PATH)
# else:
    # print("Aviso: Arquivo .env não encontrado. Usando variáveis de ambiente ou padrões.")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Tenta carregar do config.py como fallback, embora o ideal seja estar no .env
    try:
        from app.core.config import settings
        DATABASE_URL = settings.DATABASE_URL
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL não configurada nem no .env nem no config.py.")
    except ImportError:
        raise ValueError("DATABASE_URL não configurada no .env e config.py não pôde ser importado.")
    except AttributeError:
        raise ValueError("DATABASE_URL não configurada no .env e settings.DATABASE_URL não encontrado.")


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
# Removido @asynccontextmanager e ajustado para ser um async generator padrão
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit() # Commit no final se tudo correu bem
        except Exception:
            await session.rollback() # Rollback em caso de erro
            raise
        finally:
            await session.close() # Garante que a sessão seja fechada

# Comentários explicativos:
# - DATABASE_URL deve ser algo como: mysql+aiomysql://user:password@localhost:3306/dbname ou sqlite+aiosqlite:///./test.db
# - echo=True imprime as queries no console, útil para debug.
# - future=True usa a API 2.0 do SQLAlchemy.
# - get_async_db é usado com Depends(get_async_db) em rotas para injetar uma sessão do banco.

