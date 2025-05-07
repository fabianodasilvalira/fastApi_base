# app/core/dependencies.py
from typing import AsyncGenerator, Optional # AsyncGenerator para get_db assíncrono

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession # Para get_db assíncrono

from app.core import security
from app.models.user import User, UserRole # UserRole para require_admin_user
from app.db.session import get_async_db # Função para obter sessão assíncrona do DB
from app.services.user_service import user_service
from app.core.config import settings # Para tokenUrl

# Define o esquema de autenticação OAuth2
# tokenUrl deve apontar para a rota de login
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.APP_BASE_URL}/users/login") # Usar a rota completa de login

async def get_db() -> AsyncGenerator[AsyncSession, None]: # Tipo de retorno atualizado
    """Gera uma sessão de banco de dados assíncrona para ser usada como dependência."""
    async with get_async_db() as session: # Usa o get_async_db de session.py
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """Obtém o usuário atual a partir do token JWT.

    Decodifica o token, verifica se o usuário existe no banco de dados
    e retorna o objeto do usuário.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_token(token)
        if payload is None or payload.email is None: # 'sub' (email) deve estar no token
            raise credentials_exception
        # TokenData pode ser usado aqui se você tiver mais campos no payload para validar
        # token_data = TokenData(email=payload.email) 
    except JWTError:
        raise credentials_exception
    
    user = await user_service.get_user_by_email(db, email=payload.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica se o usuário atual está ativo e se o e-mail foi verificado."""
    # if not current_user.is_active: # Exemplo se houvesse um campo is_active no modelo User
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário inativo")
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # Ou 400 BAD REQUEST
            detail="Acesso negado. Seu endereço de e-mail ainda não foi verificado."
        )
    return current_user

# Dependência para verificar se o usuário é Admin
async def require_admin_user(
    current_user: User = Depends(get_current_active_user) # Agora usa o get_current_active_user atualizado
) -> User:
    """Verifica se o usuário atual (ativo e verificado) tem o papel de Admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O usuário não tem permissões de administrador"
        )
    return current_user

# Comentários em português:
# - `reusable_oauth2`: `tokenUrl` atualizado para usar a URL completa da rota de login.
# - `get_db`: Atualizado para usar `AsyncGenerator` e `get_async_db` de `app.db.session` para sessões assíncronas.
# - `get_current_user`: Permanece similar, mas garante que o `email` (subject do token) é usado para buscar o usuário.
# - `get_current_active_user`: Modificado crucialmente para verificar `current_user.is_email_verified`.
#   Se o e-mail não estiver verificado, levanta uma exceção HTTP 403 Forbidden.
#   (A verificação de `is_active` permanece comentada como exemplo, caso seja adicionada ao modelo User no futuro).
# - `require_admin_user`: Agora depende de `get_current_active_user`, garantindo que um admin também tenha o e-mail verificado.
# - As importações foram ajustadas para refletir o uso de sessões assíncronas e `AsyncSession`.

