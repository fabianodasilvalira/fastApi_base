from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List

from app import models, schemas
from app.db.session import get_async_db
from app.schemas.ocorrencia_schemas import OcorrenciaOut, OcorrenciaCreate, OcorrenciaUpdate
from app.services import ocorrencia_service
from app.core.dependencies import get_current_authorized_system, require_admin_user
from app.models.sistemas_autorizados import SistemaAutorizado

router = APIRouter()

@router.post(
    "/",
    response_model=OcorrenciaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Nova Ocorrência (Admin + Sistema Autorizado)",
    description="Cria uma nova ocorrência no sistema. Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.",
    responses={
        status.HTTP_201_CREATED: {"description": "Ocorrência criada com sucesso."},
        status.HTTP_400_BAD_REQUEST: {"description": "Dados de entrada inválidos."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_409_CONFLICT: {"description": "Conflito de dados."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Erro de validação nos dados."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def create_ocorrencia_endpoint(
    ocorrencia: OcorrenciaCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        if ocorrencia.user_id:
            user_check = await db.get(models.User, ocorrencia.user_id)
            if not user_check:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuário com ID {ocorrencia.user_id} não encontrado."
                )
        return await ocorrencia_service.create_ocorrencia(db, ocorrencia)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflito de dados. Erro: {str(e.orig)}"
        )
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de banco de dados. Erro: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro inesperado. Erro: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[OcorrenciaOut],
    summary="Listar Todas as Ocorrências (Admin + Sistema Autorizado)",
    description="Lista todas as ocorrências com paginação. Requer autenticação de usuário Admin E sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Lista de ocorrências retornada."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def read_ocorrencias_endpoint(
    skip: int = Query(0, ge=0, description="Número de registros a pular."),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros a retornar."),
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        return await ocorrencia_service.get_ocorrencias(db, skip, limit)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de banco de dados. Erro: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro inesperado. Erro: {str(e)}"
        )


@router.get(
    "/{ocorrencia_id}",
    response_model=OcorrenciaOut,
    summary="Obter Ocorrência por ID (Admin + Sistema Autorizado)",
    description="Busca uma ocorrência por ID. Requer autenticação de usuário Admin E sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Ocorrência encontrada."},
        status.HTTP_404_NOT_FOUND: {"description": "Ocorrência não encontrada."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def read_ocorrencia_endpoint(
    ocorrencia_id: int = Path(..., description="ID da ocorrência."),
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        db_ocorrencia = await ocorrencia_service.get_ocorrencia_by_id(db, ocorrencia_id)
        if db_ocorrencia is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ocorrência com ID {ocorrencia_id} não encontrada.")
        return db_ocorrencia
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de banco de dados. Erro: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro inesperado. Erro: {str(e)}"
        )


@router.put(
    "/{ocorrencia_id}",
    response_model=OcorrenciaOut,
    summary="Atualizar Ocorrência por ID (Admin + Sistema Autorizado)",
    description="Atualiza uma ocorrência existente. Requer autenticação de usuário Admin E sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Ocorrência atualizada com sucesso."},
        status.HTTP_404_NOT_FOUND: {"description": "Ocorrência ou usuário não encontrados."},
        status.HTTP_409_CONFLICT: {"description": "Conflito de dados."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Erro de validação."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def update_ocorrencia_endpoint(
    ocorrencia_update: OcorrenciaUpdate,
    ocorrencia_id: int = Path(..., description="ID da ocorrência."),
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):

    try:
        db_ocorrencia = await ocorrencia_service.get_ocorrencia_by_id(db, ocorrencia_id)
        if not db_ocorrencia:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ocorrência com ID {ocorrencia_id} não encontrada.")

        if ocorrencia_update.user_id is not None and ocorrencia_update.user_id != db_ocorrencia.user_id:
            user_check = await db.get(models.User, ocorrencia_update.user_id)
            if not user_check:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuário com ID {ocorrencia_update.user_id} não encontrado."
                )

        return await ocorrencia_service.update_ocorrencia(db, db_ocorrencia, ocorrencia_update)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflito de dados. Erro: {str(e.orig)}"
        )
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de banco de dados. Erro: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro inesperado ao atualizar a ocorrência. Erro: {str(e)}"
        )
