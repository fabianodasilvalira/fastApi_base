# Conteúdo para /home/ubuntu/fastapi_project/fastApi_base-main/app/core/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import Optional

# Lógica para encontrar o arquivo .env
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
    print(f"Carregando arquivo .env de: {ACTUAL_DOTENV_PATH}")
    load_dotenv(ACTUAL_DOTENV_PATH)
else:
    print("Aviso: Arquivo .env não encontrado nos locais esperados. Usando variáveis de ambiente ou padrões.")

class Settings(BaseSettings):
    DATABASE_URL_FROM_ENV: Optional[str] = os.getenv("DATABASE_URL")

    MYSQL_USER: str = os.getenv("MYSQL_USER", "user")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "password")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "db")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "fastapi_db")
    MYSQL_ROOT_PASSWORD: Optional[str] = os.getenv("MYSQL_ROOT_PASSWORD")

    if DATABASE_URL_FROM_ENV:
        DATABASE_URL: str = DATABASE_URL_FROM_ENV
    else:
        DATABASE_URL: str = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-please-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    MAIL_USERNAME: Optional[str] = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: Optional[str] = os.getenv("MAIL_PASSWORD")
    MAIL_FROM: Optional[str] = os.getenv("MAIL_FROM")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_SERVER: Optional[str] = os.getenv("MAIL_SERVER")
    MAIL_FROM_NAME: Optional[str] = os.getenv("MAIL_FROM_NAME", "FastAPI App")
    
    MAIL_STARTTLS: bool = str(os.getenv("MAIL_STARTTLS", "True")).lower() in ("true", "1", "t")
    MAIL_SSL_TLS: bool = str(os.getenv("MAIL_SSL_TLS", "False")).lower() in ("true", "1", "t")
    USE_CREDENTIALS: bool = str(os.getenv("USE_CREDENTIALS", "True")).lower() in ("true", "1", "t")
    VALIDATE_CERTS: bool = str(os.getenv("VALIDATE_CERTS", "True")).lower() in ("true", "1", "t")
    MAIL_DEBUG: int = int(os.getenv("MAIL_DEBUG", "0"))

    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:8000")
    # Correção no caminho do template de email para ser absoluto a partir da localização de config.py
    MAIL_TEMPLATE_FOLDER: Optional[str] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "email")

    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = int(os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS", "48"))
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_HOURS", "1"))

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads/pareceres")


    class Config:
        env_file_encoding = "utf-8"
        case_sensitive = True 
        extra = "ignore"

settings = Settings()

