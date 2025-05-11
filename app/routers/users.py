# app/routers/users.py
from typing import List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app import schemas, models
from app.core import security
from app.core.dependencies import get_db, get_current_active_user, require_admin_user, get_current_user, get_current_authorized_system
from app.models.sistemas_autorizados import SistemaAutorizado # Para type hint
from app.services.user_service import user_service
from app.core.config import settings

router = APIRouter()

# --- Rotas Públicas de Autenticação e Gerenciamento de Conta ---
@router.post("/login", response_model=schemas.Token, tags=["Usuarios"])
async def login_for_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    try:
        user = await user_service.get_user_by_email(db, email=form_data.username)
        if not user or not security.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos. Por favor, verifique suas credenciais e tente novamente.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seu e-mail ainda não foi verificado. Por favor, verifique seu e-mail antes de fazer login."
            )

        access_token = security.create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role.value}
        )
        refresh_token = security.create_refresh_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role.value}
        )
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except HTTPException as e: # Repassa HTTPExceptions
        raise e
    except Exception as e:
        # Log e (opcional)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado durante o login. Tente novamente mais tarde. Erro: {str(e)}"
        )

@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, summary="Registrar Novo Usuário e Enviar E-mail de Verificação", tags=["Usuarios"])
async def register_new_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserCreate,
) -> Any:
    try:
        existing_user_by_email = await user_service.get_user_by_email(db, email=user_in.email)
        if existing_user_by_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Um usuário com este e-mail já existe no sistema. Tente um e-mail diferente ou recupere sua senha.",
            )
        existing_user_by_cpf = await user_service.get_user_by_cpf(db, cpf=user_in.cpf)
        if existing_user_by_cpf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Um usuário com este CPF já existe no sistema. Verifique os dados ou entre em contato com o suporte.",
            )
        user = await user_service.create_user(db=db, user_in=user_in)
        # Enviar email de verificação aqui, se o user_service.create_user não o fizer
        return user
    except IntegrityError: # Especificamente para erros de constraint única (email, cpf)
        await db.rollback() # Importante reverter a transação
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflito de dados. O e-mail ou CPF fornecido já está em uso por outro usuário. Verifique os dados inseridos."
        )
    except HTTPException as e:
        raise e
    except ValueError as e: # Captura erros de validação do Pydantic ou CPF
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erro de validação nos dados fornecidos: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao registrar o usuário. Tente novamente mais tarde. Erro: {str(e)}"
        )

@router.post("/validate-registration",
    response_model=schemas.UserValidationResponse,
    summary="Validar se um usuário está cadastrado por e-mail ou CPF (Requer X-API-KEY)",
    tags=["Usuarios"],
    description="Verifica se um usuário com o CPF ou e-mail fornecido já está cadastrado no sistema. Requer autenticação de sistema via X-API-KEY.",
    responses={
        status.HTTP_200_OK: {"description": "Validação realizada com sucesso."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado (X-API-KEY inválida/ausente)."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido (Sistema não ativo ou X-API-KEY inválida)."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Erro de validação nos dados de entrada."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def validate_user_registration(
    validation_data: schemas.UserValidationRequest,
    db: AsyncSession = Depends(get_db),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system) # APENAS AUTENTICAÇÃO DE SISTEMA
) -> schemas.UserValidationResponse:
    try:
        user = None
        message = "Nenhum critério de busca fornecido."

        if validation_data.cpf:
            user = await user_service.get_user_by_cpf(db, cpf=validation_data.cpf)
            if user:
                return schemas.UserValidationResponse(
                    is_registered=True,
                    message="Usuário encontrado com o CPF fornecido.",
                    user_details=schemas.UserOut.from_orm(user)
                )

        if validation_data.email:
            user = await user_service.get_user_by_email(db, email=validation_data.email)
            if user:
                return schemas.UserValidationResponse(
                    is_registered=True,
                    message="Usuário encontrado com o e-mail fornecido.",
                    user_details=schemas.UserOut.from_orm(user)
                )

        if validation_data.cpf and validation_data.email:
            message = "Usuário não encontrado com o CPF ou e-mail fornecidos."
        elif validation_data.cpf:
            message = "Usuário não encontrado com o CPF fornecido."
        elif validation_data.email:
            message = "Usuário não encontrado com o e-mail fornecido."
        else:
             message = "Nenhum e-mail ou CPF foi fornecido para validação."

        return schemas.UserValidationResponse(is_registered=False, message=message, user_details=None)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erro de validação nos dados de entrada: {str(e)}"
        )
    except HTTPException as e: # Repassa HTTPExceptions de get_current_authorized_system
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado durante a validação do cadastro. Tente novamente. Erro: {str(e)}"
        )

@router.post("/request-email-verification", status_code=status.HTTP_200_OK, summary="Solicitar Novo E-mail de Verificação", tags=["Usuarios"])
async def request_new_email_verification(
    db: AsyncSession = Depends(get_db),
    request_body: schemas.user.EmailVerificationRequest = Body(...)
) -> Any:
    try:
        await user_service.request_new_email_verification_token(db, email=request_body.email)
        return {"message": "Se um usuário com este e-mail existir e não estiver verificado, um novo link de verificação foi enviado."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao solicitar a verificação de e-mail. Tente novamente. Erro: {str(e)}"
        )

@router.get("/verify-email/{token}", response_model=schemas.UserOut, summary="Verificar E-mail do Usuário", tags=["Usuarios"])
async def verify_user_email(
    token: str = Path(..., description="Token de verificação enviado por e-mail"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    try:
        user = await user_service.verify_email(db, token=token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de verificação inválido, expirado ou já utilizado. Solicite um novo link de verificação."
            )
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao verificar o e-mail. Tente novamente. Erro: {str(e)}"
        )

@router.post("/request-password-reset", status_code=status.HTTP_200_OK, summary="Solicitar Redefinição de Senha", tags=["Usuarios"])
async def request_password_reset(
    db: AsyncSession = Depends(get_db),
    request_body: schemas.user.PasswordResetRequest = Body(...)
) -> Any:
    try:
        await user_service.request_password_reset_for_email(db, email=request_body.email)
        return {"message": "Se um usuário com este e-mail existir, um link para redefinição de senha foi enviado."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao solicitar a redefinição de senha. Tente novamente. Erro: {str(e)}"
        )

@router.post("/reset-password/{token}", response_model=schemas.UserOut, summary="Redefinir Senha com Token", tags=["Usuarios"])
async def reset_user_password(
    token: str = Path(..., description="Token de redefinição de senha enviado por e-mail"),
    new_password_data: schemas.user.PasswordResetConfirm = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    try:
        user = await user_service.reset_password(
            db=db,
            token=token,
            new_password=new_password_data.new_password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido ou expirado. Solicite uma nova redefinição de senha."
            )
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao redefinir a senha. Tente novamente. Erro: {str(e)}"
        )


# --- Rotas de Gerenciamento de Usuário (protegidas por autenticação de usuário e/ou sistema) ---
@router.get("/me", response_model=schemas.UserOut, summary="Obter Dados do Usuário Autenticado", tags=["Usuarios"])
async def read_current_user(
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    return current_user

@router.get("/", response_model=List[schemas.UserOut], summary="Listar Todos os Usuários (Admin + Sistema Autorizado)", tags=["Usuarios"])
async def read_all_users(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
) -> Any:
    try:
        users = await user_service.get_users(db, skip=skip, limit=limit)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao listar os usuários. Tente novamente. Erro: {str(e)}"
        )

@router.get("/{user_id}", response_model=schemas.UserOut, summary="Obter Usuário por ID (Admin + Sistema Autorizado)", tags=["Usuarios"])
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
) -> Any:
    try:
        user = await user_service.get_user_by_id(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuário com ID {user_id} não encontrado.",
            )
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao buscar o usuário. Tente novamente. Erro: {str(e)}"
        )

@router.put("/{user_id}", response_model=schemas.UserOut, summary="Atualizar Usuário por ID (Admin + Sistema Autorizado)", tags=["Usuarios"])
async def update_user_by_id(
    user_id: int,
    user_in: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
) -> Any:
    try:
        db_user = await user_service.get_user_by_id(db, user_id=user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuário com ID {user_id} não encontrado para atualização.",
            )
        if user_in.email and user_in.email != db_user.email:
            existing_email_user = await user_service.get_user_by_email(db, email=user_in.email)
            if existing_email_user and existing_email_user.id != user_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="O novo e-mail fornecido já está em uso por outro usuário.")
        if user_in.cpf and user_in.cpf != db_user.cpf:
            existing_cpf_user = await user_service.get_user_by_cpf(db, cpf=user_in.cpf)
            if existing_cpf_user and existing_cpf_user.id != user_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="O novo CPF fornecido já está em uso por outro usuário.")

        updated_user = await user_service.update_user(db=db, db_user=db_user, user_in=user_in)
        return updated_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflito de dados. O e-mail ou CPF fornecido para atualização já está em uso.")
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Erro de validação nos dados fornecidos para atualização: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao atualizar o usuário. Tente novamente. Erro: {str(e)}"
        )

@router.delete("/{user_id}", response_model=schemas.UserOut, summary="Deletar Usuário por ID (Admin + Sistema Autorizado)", tags=["Usuarios"])
async def delete_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
) -> Any:
    try:
        db_user = await user_service.get_user_by_id(db, user_id=user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuário com ID {user_id} não encontrado para deleção.",
            )
        deleted_user = await user_service.delete_user(db=db, user_id=user_id)
        if not deleted_user:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao deletar usuário.")
        return deleted_user
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao deletar o usuário. Tente novamente. Erro: {str(e)}"
        )

