# app/core/dependencies.py
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.db.session import get_async_db
from app.models.user import User
from app.models.sistemas_autorizados import SistemaAutorizado
from app.services import sistemas_autorizados_service, validar_token_sistema
from app.services.user_service import get_user_by_email

#from app.models.enums import UserRole  # Certifique-se de que UserRole está definido

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.APP_BASE_URL}/api/v1/users/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_db():
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

    user = await get_user_by_email(db, email=payload.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. E-mail não verificado."
        )
    return current_user

## async def require_admin_user(
##     current_user: User = Depends(get_current_active_user)
## ) -> User:
##     if current_user.role != UserRole.ADMIN:
##    raise HTTPException(
##      status_code=status.HTTP_403_FORBIDDEN,
##      detail="Permissão de administrador necessária."
##   )
## return current_user

async def get_current_authorized_system(
    x_api_key: Optional[str] = Header(None, description="Chave de API do sistema cliente"),
    db: AsyncSession = Depends(get_db)
) -> SistemaAutorizado:
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API (X-API-KEY) não fornecida."
        )

    sistema = await validar_token_sistema(db=db, token=x_api_key)
    if sistema is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chave de API inválida ou inativa."
        )
    return sistema
