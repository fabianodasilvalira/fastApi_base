from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv(dotenv_path="/app/.env") # Caminho absoluto para o .env no container

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key_for_dev_only")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Contexto para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    email: Optional[str] = None
    # Adicionar outros campos que você queira no payload do token, como user_id ou role
    # user_id: Optional[int] = None 
    # role: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha fornecida corresponde à senha hasheada."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera o hash de uma senha."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um novo token de acesso."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um novo token de refresh."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"}) # Adiciona um tipo para diferenciar do access token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[TokenData]:
    """Decodifica um token JWT e retorna os dados do payload se válido."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub") # "sub" é o campo padrão para o sujeito (usuário)
        # user_id: Optional[int] = payload.get("user_id")
        # role: Optional[str] = payload.get("role")
        if email is None:
            return None
        return TokenData(email=email)
        # return TokenData(email=email, user_id=user_id, role=role)
    except JWTError:
        return None

# Comentários em português:
# - `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`: Configurações para JWT, carregadas do .env.
# - `pwd_context`: Utilizado para hashing e verificação de senhas com bcrypt.
# - `TokenData`: Modelo Pydantic para validar os dados esperados no payload do token.
# - `verify_password`: Compara uma senha em texto plano com um hash.
# - `get_password_hash`: Gera um hash seguro para uma senha.
# - `create_access_token`: Gera um token JWT de acesso.
# - `create_refresh_token`: Gera um token JWT de refresh (com maior tempo de expiração).
# - `decode_token`: Valida e decodifica um token JWT, retornando os dados do usuário (email) ou None se inválido.
#   O campo "sub" (subject) é comumente usado para o identificador do usuário no token.
# - O `load_dotenv` garante que as variáveis de ambiente sejam carregadas corretamente quando este módulo for importado.
#   É importante notar que o caminho para o .env deve ser o caminho dentro do container Docker.

