# app/routers/users.py
from typing import List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, models
from app.core import security
from app.core.dependencies import get_db, get_current_active_user, require_admin_user, get_current_user # Adicionado get_current_user
from app.services.user_service import user_service
from app.core.config import settings # Para mensagens de sucesso

router = APIRouter()

@router.post("/login", response_model=schemas.Token, tags=["authentication"])
async def login_for_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Realiza o login do usuário e retorna tokens de acesso e refresh.
    O usuário deve ter o e-mail verificado para poder logar.
    """
    user = await user_service.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Ou 401/403 dependendo da política
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
    """
    Registra um novo usuário no sistema e envia um e-mail de verificação.
    O usuário não é logado automaticamente e precisa verificar o e-mail.
    """
    existing_user = await user_service.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Um usuário com este email já existe no sistema.",
        )
    user = await user_service.create_user(db=db, user_in=user_in)
    # O user_service.create_user já envia o e-mail de verificação
    return user # Retorna o usuário criado (sem tokens)

@router.post("/request-email-verification", status_code=status.HTTP_200_OK, summary="Solicitar Novo E-mail de Verificação", tags=["users", "authentication"])
async def request_new_email_verification(
    db: AsyncSession = Depends(get_db),
    request_body: schemas.user.EmailVerificationRequest = Body(...)
) -> Any:
    """
    Permite que um usuário solicite um novo e-mail de verificação caso não o tenha recebido ou o token tenha expirado.
    """
    success = await user_service.request_new_email_verification_token(db, email=request_body.email)
    if not success:
        # Não vazar informação se o e-mail existe ou já está verificado. Retornar sucesso genérico.
        # Ou, para melhor UX em alguns casos, pode-se dar feedback mais específico, mas considerar implicações de segurança.
        # Por ora, vamos assumir que se não deu certo, pode ser que o usuário não exista ou já esteja verificado.
        # A lógica no service já impede reenvio para e-mails verificados.
        pass # Não levanta erro para não expor se o email existe ou não / já está verificado
    return {"message": "Se um usuário com este e-mail existir e não estiver verificado, um novo link de verificação foi enviado."}

@router.get("/verify-email/{token}", response_model=schemas.UserOut, summary="Verificar E-mail do Usuário", tags=["users", "authentication"])
async def verify_user_email(
    token: str = Path(..., description="Token de verificação enviado por e-mail"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Verifica o e-mail de um usuário usando o token fornecido na URL.
    """
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
    """
    Solicita o envio de um e-mail para redefinição de senha.
    """
    success = await user_service.request_password_reset_for_email(db, email=request_body.email)
    if not success:
        # Não vazar informação se o e-mail existe. Retornar sucesso genérico.
        pass
    return {"message": "Se um usuário com este e-mail existir, um link para redefinição de senha foi enviado."}

@router.post("/reset-password/{token}", response_model=schemas.UserOut, summary="Redefinir Senha com Token", tags=["users", "authentication"])
async def reset_user_password(
    token: str = Path(..., description="Token de redefinição de senha enviado por e-mail"),
    new_password_data: schemas.user.PasswordResetConfirm = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Redefine a senha do usuário utilizando o token e a nova senha fornecida.
    """
    user = await user_service.reset_password(db, token=token, new_password=new_password_data.new_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de redefinição de senha inválido, expirado ou já utilizado."
        )
    # Opcional: Enviar um e-mail de confirmação de que a senha foi alterada.
    return user

# Rotas de Gerenciamento de Usuário (protegidas)
@router.get("/me", response_model=schemas.UserOut, summary="Obter Dados do Usuário Autenticado", tags=["users"])
async def read_current_user(
    current_user: models.user = Depends(get_current_active_user) # get_current_active_user já verifica se está ativo e verificado
) -> Any:
    """
    Retorna os dados do usuário autenticado e ativo.
    """
    return current_user

@router.get("/{user_id}", response_model=schemas.UserOut, dependencies=[Depends(require_admin_user)], summary="Obter Usuário por ID (Admin)", tags=["users"])
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retorna os dados de um usuário específico pelo ID (somente Admin).
    """
    user = await user_service.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )
    return user

@router.put("/{user_id}", response_model=schemas.UserOut, dependencies=[Depends(require_admin_user)], summary="Atualizar Usuário por ID (Admin)", tags=["users"])
async def update_user_by_id(
    user_id: int,
    user_in: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Atualiza os dados de um usuário específico pelo ID (somente Admin).
    """
    db_user = await user_service.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado para atualização.",
        )
    updated_user = await user_service.update_user(db=db, db_user=db_user, user_in=user_in)
    return updated_user

@router.get("/", response_model=List[schemas.UserOut], dependencies=[Depends(require_admin_user)], summary="Listar Todos os Usuários (Admin)", tags=["users"])
async def read_all_users(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
) -> Any:
    """
    Retorna uma lista de todos os usuários com paginação (somente Admin).
    """
    users = await user_service.get_users(db, skip=skip, limit=limit)
    return users


# Comentários em português:
# - Rota `/login` agora verifica `user.is_email_verified`.
# - Rota `/register` modificada: registra o usuário e o `user_service` envia o e-mail de verificação. Não retorna tokens.
# - Nova rota `POST /users/request-email-verification`: Para solicitar um novo e-mail de verificação.
# - Nova rota `GET /users/verify-email/{token}`: Para o usuário clicar no link do e-mail e verificar a conta.
# - Nova rota `POST /users/request-password-reset`: Para solicitar um e-mail de redefinição de senha.
# - Nova rota `POST /users/reset-password/{token}`: Para o usuário definir uma nova senha usando o token.
# - A dependência `get_current_active_user` (a ser modificada em `dependencies.py`) deve agora também checar `is_email_verified`.
# - Adicionadas tags "authentication" para agrupar rotas relacionadas na documentação.
# - Adicionados `summary` para melhor descrição na documentação OpenAPI.

