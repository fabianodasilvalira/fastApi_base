from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List
import logging

from app import models, schemas
from app.db.session import get_async_db
from app.schemas.ocorrencia_schemas import OcorrenciaOut, OcorrenciaCreate
from app.services import ocorrencia_service
from app.core.dependencies import get_current_authorized_system, require_admin_user
from app.models.sistemas_autorizados import SistemaAutorizado

router = APIRouter()
logger = logging.getLogger(__name__)

# Função utilitária para tratamento de exceções
def handle_db_exception(e: Exception, default_message: str = "Erro inesperado"):
    if isinstance(e, IntegrityError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflito de dados. Erro: {str(e.orig)}"
        )
    elif isinstance(e, SQLAlchemyError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de banco de dados. Erro: {str(e)}"
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{default_message}. Erro: {str(e)}"
    )

# Rota para criar uma nova ocorrência
@router.post(
    "/criar",
    response_model=OcorrenciaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Nova Ocorrência (Admin + Sistema Autorizado)",
    description="""Requer:
- Autenticação do sistema via `X-API-KEY`
- Autenticação de usuário com perfil **Admin**

Cria uma nova ocorrência no sistema.
""",
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
async def criar_ocorrencia(
    ocorrencia: OcorrenciaCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        return await ocorrencia_service.create_ocorrencia(db, ocorrencia)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao criar ocorrência")
        await db.rollback()
        raise handle_db_exception(e, "Erro ao criar ocorrência")

# Rota para listar todas as ocorrências
@router.get(
    "/listar",
    response_model=List[OcorrenciaOut],
    summary="Listar Todas as Ocorrências (Admin + Sistema Autorizado)",
    description="""Requer:
- Autenticação do sistema via `X-API-KEY`
- Autenticação de usuário com perfil **Admin**

Lista todas as ocorrências com paginação.
""",
    responses={
        status.HTTP_200_OK: {"description": "Lista de ocorrências retornada."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def listar_ocorrencias(
    skip: int = Query(0, ge=0, description="Número de registros a pular."),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros a retornar."),
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        return await ocorrencia_service.get_ocorrencias(db, skip, limit)
    except Exception as e:
        logger.exception("Erro ao listar ocorrências")
        raise handle_db_exception(e, "Erro ao listar ocorrências")

# Rota para obter uma ocorrência por ID
@router.get(
    "/{ocorrencia_id}/detalhar",
    response_model=OcorrenciaOut,
    summary="Obter Ocorrência por ID (Admin + Sistema Autorizado)",
    description="""Requer:
- Autenticação do sistema via `X-API-KEY`
- Autenticação de usuário com perfil **Admin**

Busca uma ocorrência por ID.
""",
    responses={
        status.HTTP_200_OK: {"description": "Ocorrência encontrada."},
        status.HTTP_404_NOT_FOUND: {"description": "Ocorrência não encontrada."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def obter_ocorrencia_por_id(
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
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro ao buscar ocorrência por ID")
        raise handle_db_exception(e, "Erro ao buscar ocorrência por ID")
