import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Optional

# Caminho para o arquivo .env na raiz do projeto (um nível acima de /app)
# No Docker, o .env da raiz do projeto local é montado em /app/.env
DOTENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if not os.path.exists(DOTENV_PATH):
    # Se estiver rodando localmente e o .env estiver na raiz do /app (onde está o main.py)
    DOTENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.exists(DOTENV_PATH):
        # Se estiver no contexto do Docker, onde o WORKDIR é /app
        DOTENV_PATH = "/app/.env"

load_dotenv(DOTENV_PATH)


class Settings(BaseSettings):
    # Configurações da Aplicação e JWT (já existentes)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+aiomysql://user:password@db:3306/fastapi_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key_for_dev_only")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Configurações de Banco de Dados (adicionadas conforme sua necessidade)
    MYSQL_USER: str = os.getenv("MYSQL_USER", "default_user")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "default_password")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "fastapi_db")

    # Atualiza a URL do banco de dados com base nas variáveis MYSQL_* definidas
    DATABASE_URL: str = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@db:3306/{MYSQL_DATABASE}"

    # Configurações de E-mail
    MAIL_USERNAME: Optional[str] = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: Optional[str] = os.getenv("MAIL_PASSWORD")
    MYSQL_ROOT_PASSWORD: Optional[str] = os.getenv("MYSQL_ROOT_PASSWORD")
    MAIL_FROM: Optional[str] = os.getenv("MAIL_FROM")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_SERVER: Optional[str] = os.getenv("MAIL_SERVER")
    MAIL_FROM_NAME: Optional[str] = os.getenv("MAIL_FROM_NAME", "Meu App")
    MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"
    USE_CREDENTIALS: bool = os.getenv("USE_CREDENTIALS", "True").lower() == "true"
    VALIDATE_CERTS: bool = os.getenv("VALIDATE_CERTS", "True").lower() == "true"
    MAIL_DEBUG: int = int(os.getenv("MAIL_DEBUG", "0"))  # 0 para não debug, 1 para debug

    # URL base da aplicação para links em e-mails
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:8000")

    # Configurações para templates de e-mail (se usar fastapi-mail com templates)
    MAIL_TEMPLATE_FOLDER: Optional[str] = os.path.join(os.path.dirname(__file__), "..", "templates", "email")

    # Token lifetimes
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1

    class Config:
        env_file = DOTENV_PATH
        env_file_encoding = "utf-8"
        case_sensitive = True  # Mantém a sensibilidade de maiúsculas/minúsculas das variáveis de ambiente
        extra = "ignore"  # ou "allow"

settings = Settings()

# Comentários em português:
# - `Settings`: Classe Pydantic para carregar e validar todas as configurações da aplicação a partir de variáveis de ambiente.
# - `DOTENV_PATH`: Tenta localizar o arquivo .env. No Docker, ele é montado em `/app/.env`.
# - As configurações de banco de dados (MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE) são carregadas do `.env` e usadas para construir a URL do banco de dados.
# - As configurações de e-mail são carregadas do `.env`.
# - `APP_BASE_URL`: URL base usada para construir links completos em e-mails (ex: link de verificação).
# - `MAIL_TEMPLATE_FOLDER`: Define o local para templates de e-mail, se forem usados.
# - `EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS` e `PASSWORD_RESET_TOKEN_EXPIRE_HOURS`: Tempos de expiração para os tokens.
# - `settings`: Instância global da classe `Settings` para ser importada e usada em toda a aplicação.
