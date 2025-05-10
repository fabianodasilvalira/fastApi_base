# app/routers/users.py
from typing import List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, models
from app.core import security
from app.core.dependencies import get_db, get_current_active_user, require_admin_user, get_current_user, get_current_authorized_system # Adicionado get_current_authorized_system
from app.models.sistemas_autorizados import SistemaAutorizado # Para type hint
from app.services.user_service import user_service
from app.core.config import settings

router = APIRouter()

# --- Rotas Públicas de Autenticação e Gerenciamento de Conta ---
@router.post("/login", response_model=schemas.Token, tags=["authentication"])
async def login_for_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = await user_service.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seu e-mail ainda não foi verificado. Por favor, verifique seu e-mail antes de logar."
        )
    
    access_token = security.create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role.value}
    )
    refresh_token = security.create_refresh_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role.value}
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, summary="Registrar Novo Usuário e Enviar E-mail de Verificação", tags=["users", "authentication"])
async def register_new_user(
    *, 
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserCreate,
) -> Any:
    existing_user = await user_service.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Um usuário com este email já existe no sistema.",
        )
    user = await user_service.create_user(db=db, user_in=user_in)
    return user

@router.post("/request-email-verification", status_code=status.HTTP_200_OK, summary="Solicitar Novo E-mail de Verificação", tags=["users", "authentication"])
async def request_new_email_verification(
    db: AsyncSession = Depends(get_db),
    request_body: schemas.user.EmailVerificationRequest = Body(...)
) -> Any:
    await user_service.request_new_email_verification_token(db, email=request_body.email)
    return {"message": "Se um usuário com este e-mail existir e não estiver verificado, um novo link de verificação foi enviado."}

@router.get("/verify-email/{token}", response_model=schemas.UserOut, summary="Verificar E-mail do Usuário", tags=["users", "authentication"])
async def verify_user_email(
    token: str = Path(..., description="Token de verificação enviado por e-mail"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    user = await user_service.verify_email(db, token=token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de verificação inválido, expirado ou já utilizado."
        )
    return user

@router.post("/request-password-reset", status_code=status.HTTP_200_OK, summary="Solicitar Redefinição de Senha", tags=["users", "authentication"])
async def request_password_reset(
    db: AsyncSession = Depends(get_db),
    request_body: schemas.user.PasswordResetRequest = Body(...)
) -> Any:
    await user_service.request_password_reset_for_email(db, email=request_body.email)
    return {"message": "Se um usuário com este e-mail existir, um link para redefinição de senha foi enviado."}

@router.post("/reset-password/{token}", response_model=schemas.UserOut, summary="Redefinir Senha com Token", tags=["users", "authentication"])
async def reset_user_password(
    token: str = Path(..., description="Token de redefinição de senha enviado por e-mail"),
    new_password_data: schemas.user.PasswordResetConfirm = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    user = await user_service.reset_password(db, token=token, new_password=new_password_data.new_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de redefinição de senha inválido, expirado ou já utilizado."
        )
    return user

# --- Rotas de Gerenciamento de Usuário (protegidas por autenticação de usuário e/ou sistema) ---
@router.get("/me", response_model=schemas.UserOut, summary="Obter Dados do Usuário Autenticado", tags=["users"])
async def read_current_user(
    # Esta rota é para o usuário obter seus próprios dados, não precisa de X-API-KEY
    current_user: models.User = Depends(get_current_active_user) 
) -> Any:
    return current_user

# As rotas de gerenciamento de usuários abaixo (listar, obter por ID, atualizar, deletar)
# são geralmente acessadas por um sistema de administração ou outro sistema autorizado.
# Portanto, protegemos com require_admin_user E get_current_authorized_system.

@router.get("/", response_model=List[schemas.UserOut], summary="Listar Todos os Usuários (Admin + Sistema Autorizado)", tags=["users"])
async def read_all_users(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    admin_user: models.User = Depends(require_admin_user), # Requer usuário admin logado
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system) # Requer X-API-KEY válido
) -> Any:
    users = await user_service.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.UserOut, summary="Obter Usuário por ID (Admin + Sistema Autorizado)", tags=["users"])
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
) -> Any:
    user = await user_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )
    return user

@router.put("/{user_id}", response_model=schemas.UserOut, summary="Atualizar Usuário por ID (Admin + Sistema Autorizado)", tags=["users"])
async def update_user_by_id(
    user_id: int,
    user_in: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
) -> Any:
    db_user = await user_service.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado para atualização.",
        )
    updated_user = await user_service.update_user(db=db, db_user=db_user, user_in=user_in)
    return updated_user

# Adicionar rota DELETE para usuários (Admin + Sistema Autorizado)
@router.delete("/{user_id}", response_model=schemas.UserOut, summary="Deletar Usuário por ID (Admin + Sistema Autorizado)", tags=["users"])
async def delete_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
) -> Any:
    db_user = await user_service.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado para deleção.",
        )
    # Implementar a lógica de deleção no service ou aqui
    # Por exemplo, marcar como inativo ou realmente deletar
    # Aqui, vamos assumir que o service tem um método delete_user
    # Se não, adaptar: await db.delete(db_user); await db.commit()
    deleted_user = await user_service.delete_user(db=db, user_id=user_id) # Supondo que delete_user exista e retorne o usuário deletado
    if not deleted_user:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao deletar usuário.")
    return deleted_user

