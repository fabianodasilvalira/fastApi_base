from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List

from app import models, schemas
from app.db.session import get_async_db
from app.schemas.ocorrencia_schemas import OcorrenciaOut, OcorrenciaCreate, OcorrenciaUpdate, OcorrenciaFilterParams, \
    OcorrenciaWithPareceresOut
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
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        # ⚠️ Verifica e busca o usuário, se fornecido
        user_data = None
        if ocorrencia.user_id:
            user_data = await db.get(models.User, ocorrencia.user_id)
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuário com ID {ocorrencia.user_id} não encontrado."
                )

        # 🛠️ Monta novo objeto com valores fixos e dados do usuário
        ocorrencia_dict = ocorrencia.model_dump()
        ocorrencia_dict.update({
            "situacao_ocorrencia_id": 1,
            "regiao_id": 6,
            "programa_id": 6,
            "tipo_atendimento_id": 10,
        })

        # Se encontrou o usuário, preenche nome_completo e fones
        if user_data:
            ocorrencia_dict.update({
                "nome_completo": user_data.nome_completo,
                "fone1": user_data.fone1,
                "fone2": user_data.fone2
            })

        # Cria a ocorrência
        return await ocorrencia_service.create_ocorrencia(db, OcorrenciaCreate(**ocorrencia_dict))

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
    skip: int = Query(0, ge=0, description="Registro inicial a partir do qual os resultados serão exibidos (usado para paginação).."),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros a retornar."),
    db: AsyncSession = Depends(get_async_db),
    #current_user: models.User = Depends(require_admin_user),
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

# Nova rota: Listar ocorrências por usuario_id
@router.get(
    "/por-usuario/{user_id}",
    response_model=List[OcorrenciaOut],
    summary="Listar Ocorrências por ID do Usuário (Admin + Sistema Autorizado)",
    description="Lista ocorrências filtradas pelo ID do usuário criador, com filtros opcionais. Requer autenticação de usuário Admin E sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Lista de ocorrências retornada."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def read_ocorrencias_by_user_id_endpoint(
    user_id: int = Path(..., description="ID do usuário criador da ocorrência."),
    skip: int = Query(0, ge=0, description="Registro inicial a partir do qual os resultados serão exibidos (usado para paginação).."),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros a retornar."),
    filters: OcorrenciaFilterParams = Depends(),
    db: AsyncSession = Depends(get_async_db),
    #current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        return await ocorrencia_service.get_ocorrencias_by_user_id(db, user_id=user_id, filters=filters, skip=skip, limit=limit)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro de banco de dados: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro inesperado: {str(e)}")

# Nova rota: Listar ocorrências por usuario_encaminhado
@router.get(
    "/por-usuario-encaminhado/{usuario_encaminhado_id}",
    response_model=List[OcorrenciaOut],
    summary="Listar Ocorrências por ID do Usuário Encaminhado (Admin + Sistema Autorizado)",
    description="Lista ocorrências filtradas pelo ID do usuário para quem foi encaminhada (padrão não arquivadas), com filtros opcionais. Requer autenticação de usuário Admin E sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Lista de ocorrências retornada."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def read_ocorrencias_by_usuario_encaminhado_endpoint(
    usuario_encaminhado_id: int = Path(..., description="ID do usuário para quem a ocorrência foi encaminhada."),
    skip: int = Query(0, ge=0, description="Registro inicial a partir do qual os resultados serão exibidos (usado para paginação).."),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros a retornar."),
    filters: OcorrenciaFilterParams = Depends(), # O service aplicará arquivado='N' por padrão se não vier em filters
    db: AsyncSession = Depends(get_async_db),
    #current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        return await ocorrencia_service.get_ocorrencias_by_usuario_encaminhado(db, usuario_encaminhado_id=usuario_encaminhado_id, filters=filters, skip=skip, limit=limit)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro de banco de dados: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro inesperado: {str(e)}")

# Nova rota: Listar ocorrências por orgao_encaminhado
@router.get(
    "/por-orgao-encaminhado/{orgao_encaminhado_id}",
    response_model=List[OcorrenciaOut],
    summary="Listar Ocorrências por ID do Órgão Encaminhado (Admin + Sistema Autorizado)",
    description="Lista ocorrências filtradas pelo ID do órgão para quem foi encaminhada (padrão não arquivadas), com filtros opcionais. Requer autenticação de usuário Admin E sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Lista de ocorrências retornada."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def read_ocorrencias_by_orgao_encaminhado_endpoint(
    orgao_encaminhado_id: int = Path(..., description="ID do órgão para quem a ocorrência foi encaminhada."),
    skip: int = Query(0, ge=0, description="Registro inicial a partir do qual os resultados serão exibidos (usado para paginação).."),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros a retornar."),
    filters: OcorrenciaFilterParams = Depends(), # O service aplicará arquivado='N' por padrão se não vier em filters
    db: AsyncSession = Depends(get_async_db),
    #current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        return await ocorrencia_service.get_ocorrencias_by_orgao_encaminhado(db, orgao_encaminhado_id=orgao_encaminhado_id, filters=filters, skip=skip, limit=limit)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro de banco de dados: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro inesperado: {str(e)}")

# Nova rota: Listar ocorrencia_id com todos pareceres
@router.get(
    "/{ocorrencia_id}/com-pareceres",
    response_model=OcorrenciaWithPareceresOut, # Schema de resposta que inclui pareceres
    summary="Obter Ocorrência por ID com Todos os Pareceres (Admin + Sistema Autorizado)",
    description="Busca uma ocorrência específica por ID e inclui todos os seus pareceres. Filtros opcionais se aplicam à ocorrência. Requer autenticação de usuário Admin E sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Ocorrência com pareceres encontrada."},
        status.HTTP_404_NOT_FOUND: {"description": "Ocorrência não encontrada."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def read_ocorrencia_with_pareceres_endpoint(
    ocorrencia_id: int = Path(..., description="ID da ocorrência."),
    filters: OcorrenciaFilterParams = Depends(), # Filtros se aplicam à ocorrência principal
    db: AsyncSession = Depends(get_async_db),
    #current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        # O service get_ocorrencia_by_id_with_pareceres foi atualizado para receber 'filters'
        # e o service lida com o padrão 'arquivado=N' para a ocorrência principal se não especificado
        db_ocorrencia = await ocorrencia_service.get_ocorrencia_by_id_with_pareceres(db, ocorrencia_id=ocorrencia_id, filters=filters)
        if db_ocorrencia is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ocorrência com ID {ocorrencia_id} não encontrada ou não corresponde aos filtros.")
        return db_ocorrencia
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro de banco de dados: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro inesperado: {str(e)}")


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
    #current_user: models.User = Depends(require_admin_user),
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
    #current_user: models.User = Depends(require_admin_user),
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


