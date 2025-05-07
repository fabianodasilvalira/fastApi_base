import sys
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import os
from dotenv import load_dotenv
import asyncio

# Carregar as variáveis do ambiente
load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from app.db import Base
from app.models import User


# Recupera DATABASE_URL do .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Configura a engine assíncrona
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Aplica a URL no config do Alembic
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Configura logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importa os modelos
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_async_engine(DATABASE_URL)

    async with connectable.connect() as connection:
        # Configura o contexto
        def callback(sync_conn):
            context.configure(
                connection=sync_conn,
                target_metadata=target_metadata
            )
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(callback)

if context.is_offline_mode():
    run_migrations_offline()
else:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_migrations_online())