from logging.config import fileConfig
import os
import sys
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Adiciona o diretório raiz do projeto ao sys.path
# Para que o Alembic encontre os módulos da aplicação (ex: app.models)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.db.base_class import Base  # Importa a Base dos seus modelos
from app.models.user import User # Importa seus modelos SQLAlchemy aqui
# Adicione outras importações de modelos se houver mais

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Seta a URL do banco de dados a partir da variável de ambiente
# Isso sobrescreve o sqlalchemy.url do alembic.ini se estiver usando variáveis de ambiente
# para configurar a URL do banco de dados em produção/docker.
database_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata # Aponta para o metadata da sua Base

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True, # Adicionado para detectar mudanças de tipo de coluna
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True, # Adicionado para detectar mudanças de tipo de coluna
            render_as_batch=True # Adicionado para SQLite e outros DBs que não suportam ALTER direto
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
