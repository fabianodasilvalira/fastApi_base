# app/core/dependencies.py
from typing import AsyncGenerator, Optional # AsyncGenerator para get_db assíncrono

from fastapi import Depends, HTTPException, status, Header # Adicionado Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession # Para get_db assíncrono

from app.core import security
from app.models.user import User, UserRole # UserRole para require_admin_user
from app.models.sistemas_autorizados import SistemaAutorizado # Modelo para autenticação de sistema
from app.db.session import get_async_db # Função para obter sessão assíncrona do DB
from app.services import user_service # Mantido para autenticação de usuário
from app.services import sistemas_autorizados_service # Para validar token de sistema
from app.core.config import settings # Para tokenUrl

# Define o esquema de autenticação OAuth2
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.APP_BASE_URL}/api/v1/users/login") # Corrigido para o prefixo da API

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Gera uma sessão de banco de dados assíncrona para ser usada como dependência."""
    # A lógica de get_async_db já lida com try/except/finally e commit/rollback/close
    async for session in get_async_db(): # Iterar sobre o gerador
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais do usuário",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_token(token)
        if payload is None or payload.email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await user_service.get_user_by_email(db, email=payload.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Seu endereço de e-mail ainda não foi verificado."
        )
    # Adicionar verificação de is_active se existir no modelo User
    # if hasattr(current_user, 'is_active') and not current_user.is_active:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário inativo")
    return current_user

async def require_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O usuário não tem permissões de administrador"
        )
    return current_user

# Nova dependência para autenticação de sistema via X-API-KEY
async def get_current_authorized_system(
    x_api_key: Optional[str] = Header(None, description="Chave de API do sistema cliente"),
    db: AsyncSession = Depends(get_db)
) -> SistemaAutorizado:
    """
    Valida o X-API-KEY fornecido no header.
    Retorna o objeto SistemaAutorizado se o token for válido e ativo.
    Levanta HTTPException 401 ou 403 em caso de falha.
    """
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API (X-API-KEY) não fornecida no header."
        )
    
    sistema = await sistemas_autorizados_service.validar_token_sistema(db=db, token=x_api_key)
    
    if sistema is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # Usar 403 para chave inválida/inativa após tentativa
            detail="Chave de API (X-API-KEY) inválida, inativa ou não autorizada."
        )
    return sistema

