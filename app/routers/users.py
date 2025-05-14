# app/routers/users.py
from asyncio.log import logger
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import schemas, models
from app.core.dependencies import get_db, require_admin_user, get_current_authorized_system
from app.models import SistemaAutorizado
from app.schemas.user import UserOut, UserCreate, UserUpdate, UserCheckRequest
from app.services import validar_token_sistema
from app.services.user_service import user_service

router = APIRouter()


@router.get(
    "/",
    response_model=List[UserOut],
    summary="Listar todos os usuários",
    description="Retorna uma lista paginada de todos os usuários cadastrados no sistema."
)
async def obter_todos_usuarios(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Número de registros a pular para paginação."),
    limit: int = Query(10, ge=1, description="Número máximo de registros a retornar.")
) -> List[UserOut]:
    usuarios = await user_service.get_all_users(db, skip=skip, limit=limit)
    return usuarios


@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Obter usuário por ID",
    description="Busca e retorna os dados de um usuário específico com base no ID fornecido."
)
async def obter_usuario_por_id(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> Any:
    usuario = await user_service.get_user_by_id(db, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return usuario


@router.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo usuário",
    description="Cria um novo usuário no sistema. Valida se o e-mail, CPF ou username já estão cadastrados."
)
async def criar_usuario(
    usuario_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    try:
        return await user_service.create_user(db=db, user_in=usuario_in)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail, CPF ou username já cadastrado."
        )
    except Exception as e:
        await db.rollback()
        print(f"Erro ao criar o usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao criar o usuário. Tente novamente. Erro: {str(e)}"
        )


@router.put(
    "/{user_id}",
    response_model=UserOut,
    summary="Atualizar dados do usuário",
    description="Atualiza os dados de um usuário existente com base no ID fornecido."
)
async def atualizar_usuario(
    user_id: int,
    usuario_in: UserUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    usuario = await user_service.get_user_by_id(db, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return await user_service.update_user(db=db, db_user=usuario, user_in=usuario_in)


@router.post(
    "/verificar",
    summary="Verificar existência de usuário por CPF e telefone (Sistema Autorizado)",
    description="Verifica se um usuário já está cadastrado no sistema com base no CPF e número de telefone. Requer autenticação por X-API-KEY de sistema autorizado."
)
async def verificar_usuario_existe(
    usuario_check: UserCheckRequest,
    db: AsyncSession = Depends(get_db),
    sistema_autorizado: models.SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        result = await db.execute(
            select(models.User).filter(
                models.User.cpf == usuario_check.cpf,
                models.User.phone == usuario_check.phone
            )
        )
        usuario = result.scalars().first()

        if usuario:
            return {"mensagem": "Usuário já cadastrado no sistema"}
        return {"mensagem": "Usuário não cadastrado"}

    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao verificar usuário por CPF: {usuario_check.cpf} e telefone: {usuario_check.phone} - Erro: {e}")
        raise HTTPException(status_code=500, detail="Erro ao acessar o banco de dados.")
