from fastapi import APIRouter, Depends, HTTPException, Header, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List, Optional

from app import models, schemas # Import models for type hinting
from app.schemas.sistemas_autorizados_schemas import SistemaAutorizadoComTokenResponse, SistemaAutorizadoResponse
from app.services import sistemas_autorizados_service
from app.db.session import get_async_db
from app.core.dependencies import get_current_authorized_system, require_admin_user 

router = APIRouter()

@router.post(
    "/", 
    response_model=SistemaAutorizadoComTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Novo Sistema Autorizado (Admin)",
    description="Registra um novo sistema cliente e gera um token de API para ele. Requer autenticação de usuário Admin.",
    responses={
        status.HTTP_201_CREATED: {"description": "Sistema autorizado criado com sucesso e token gerado."},
        status.HTTP_400_BAD_REQUEST: {"description": "Dados de entrada inválidos."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado (Token de usuário admin inválido/ausente)."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido (Usuário não é admin)."},
        status.HTTP_409_CONFLICT: {"description": "Conflito de dados (ex: nome do sistema já existe)."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Entidade não processável (erro de validação nos dados)."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def criar_sistema_autorizado_endpoint(
    sistema: schemas.SistemaAutorizadoCreate, 
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user)
):
    try:
        # Verificar se já existe um sistema com o mesmo nome, se for uma constraint
        # Esta verificação pode ser mais robusta no service ou com constraints de DB
        # Por ora, o service.criar_sistema_autorizado pode levantar IntegrityError
        db_sistema = await sistemas_autorizados_service.criar_sistema_autorizado(db=db, sistema=sistema)
        return db_sistema
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Não foi possível criar o sistema autorizado devido a um conflito de dados (ex: nome já existe). Erro: {str(e.orig)}"
        )
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro de banco de dados ao criar o sistema autorizado. Tente novamente. Erro: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao criar o sistema autorizado. Tente novamente. Erro: {str(e)}"
        )

@router.get(
    "/", 
    response_model=List[SistemaAutorizadoResponse],
    summary="Listar Sistemas Autorizados (Admin + Sistema Autorizado)",
    description="Lista os sistemas clientes registrados (não expõe os tokens). Requer autenticação de usuário Admin E X-API-KEY de sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Lista de sistemas autorizados retornada com sucesso."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def listar_sistemas_autorizados_endpoint(
    skip: int = Query(0, ge=0, description="Número de registros a pular para paginação."), 
    limit: int = Query(100, ge=1, le=200, description="Número máximo de registros a retornar."), 
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: models.SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        sistemas = await sistemas_autorizados_service.get_sistemas_autorizados(db, skip=skip, limit=limit)
        return sistemas
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro de banco de dados ao listar os sistemas autorizados. Tente novamente. Erro: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao listar os sistemas autorizados. Tente novamente. Erro: {str(e)}"
        )

@router.get(
    "/{sistema_id}", 
    response_model=SistemaAutorizadoResponse,
    summary="Obter Sistema Autorizado por ID (Admin + Sistema Autorizado)",
    description="Obtém dados de um sistema autorizado específico pelo ID. Requer autenticação de usuário Admin E X-API-KEY de sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Sistema autorizado encontrado e retornado com sucesso."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_404_NOT_FOUND: {"description": "Sistema autorizado não encontrado."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def obter_sistema_autorizado_endpoint(
    sistema_id: int = Path(..., description="ID do sistema autorizado a ser buscado."),
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: models.SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        db_sistema = await sistemas_autorizados_service.get_sistema_autorizado_by_id(db, sistema_id=sistema_id)
        if db_sistema is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sistema autorizado com ID {sistema_id} não encontrado.")
        return db_sistema
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro de banco de dados ao buscar o sistema autorizado {sistema_id}. Tente novamente. Erro: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao buscar o sistema autorizado {sistema_id}. Tente novamente. Erro: {str(e)}"
        )

@router.post(
    "/validar-token/", 
    response_model=SistemaAutorizadoResponse,
    summary="Validar Token de Sistema (Requer X-API-KEY)",
    description="Valida um token de API de sistema cliente (X-API-KEY fornecido no header). Se válido e ativo, retorna os dados do sistema e atualiza sua última atividade. Requer X-API-KEY de sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Token válido, dados do sistema retornados."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado (X-API-KEY inválida, ausente ou sistema inativo)."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def validar_token_endpoint(
    # A dependência get_current_authorized_system já trata a extração e validação do X-API-KEY.
    # Ela levantará HTTPException 401/403 se o token for inválido, ausente ou sistema inativo.
    validating_system: models.SistemaAutorizado = Depends(get_current_authorized_system) 
):
    # Se chegou aqui, a dependência get_current_authorized_system já validou o token
    # e o sistema está ativo. O service também atualizou a última atividade.
    try:
        return validating_system
    except Exception as e: # Captura genérica para o caso improvável de erro após a dependência
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao processar a validação do token. Tente novamente. Erro: {str(e)}"
        )

@router.put(
    "/{sistema_id}/ultima-atividade/", 
    response_model=SistemaAutorizadoResponse,
    summary="Atualizar Última Atividade do Sistema (Admin + Sistema Autorizado)",
    description="Atualiza o campo 'ultima_atividade' de um sistema cliente específico. Requer autenticação de usuário Admin E X-API-KEY de sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Última atividade atualizada com sucesso."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_404_NOT_FOUND: {"description": "Sistema não encontrado para atualizar última atividade."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def atualizar_ultima_atividade_endpoint(
    sistema_id: int = Path(..., description="ID do sistema para atualizar a última atividade."), 
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: models.SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        sistema_atualizado = await sistemas_autorizados_service.atualizar_ultima_atividade_sistema(db, sistema_id=sistema_id)
        if sistema_atualizado is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sistema com ID {sistema_id} não encontrado para atualizar última atividade.")
        return sistema_atualizado
    except SQLAlchemyError as e:
        await db.rollback() # Embora o service possa não ter feito commit se retornou None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro de banco de dados ao atualizar a última atividade do sistema {sistema_id}. Tente novamente. Erro: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao atualizar a última atividade do sistema {sistema_id}. Tente novamente. Erro: {str(e)}"
        )

@router.put(
    "/{sistema_id}", 
    response_model=SistemaAutorizadoResponse,
    summary="Atualizar Sistema Autorizado (Admin + Sistema Autorizado)",
    description="Atualiza dados de um sistema autorizado. Requer autenticação de usuário Admin E X-API-KEY de sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Sistema autorizado atualizado com sucesso."},
        status.HTTP_400_BAD_REQUEST: {"description": "Dados de entrada inválidos."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_404_NOT_FOUND: {"description": "Sistema autorizado não encontrado para atualização."},
        status.HTTP_409_CONFLICT: {"description": "Conflito de dados (ex: nome duplicado)."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Entidade não processável."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def atualizar_sistema_autorizado_endpoint(
    sistema_update: schemas.SistemaAutorizadoUpdate,
    sistema_id: int = Path(..., description="ID do sistema autorizado a ser atualizado."),
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: models.SistemaAutorizado = Depends(get_current_authorized_system)
):

    try:
        db_sistema = await sistemas_autorizados_service.get_sistema_autorizado_by_id(db, sistema_id=sistema_id)
        if db_sistema is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sistema autorizado com ID {sistema_id} não encontrado para atualização.")
        
        # Adicionar verificação de nome duplicado se o nome for alterado e houver constraint
        if sistema_update.nome and sistema_update.nome != db_sistema.nome:
            check_existing_name = await db.execute(select(models.SistemaAutorizado).where(models.SistemaAutorizado.nome == sistema_update.nome, models.SistemaAutorizado.id != sistema_id))
            if check_existing_name.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Já existe um sistema autorizado com o nome '{sistema_update.nome}'.")

        updated_sistema = await sistemas_autorizados_service.update_sistema_autorizado(db, db_sistema, sistema_update)
        return updated_sistema
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Não foi possível atualizar o sistema autorizado {sistema_id} devido a um conflito de dados. Erro: {str(e.orig)}"
        )
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro de banco de dados ao atualizar o sistema autorizado {sistema_id}. Tente novamente. Erro: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao atualizar o sistema autorizado {sistema_id}. Tente novamente. Erro: {str(e)}"
        )

@router.delete(
    "/{sistema_id}",
    response_model=SistemaAutorizadoResponse, # Ou um schema de confirmação
    summary="Deletar Sistema Autorizado (Admin + Sistema Autorizado)",
    description="Deleta um sistema autorizado. Requer autenticação de usuário Admin E X-API-KEY de sistema autorizado.",
    responses={
        status.HTTP_200_OK: {"description": "Sistema autorizado deletado com sucesso."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_404_NOT_FOUND: {"description": "Sistema autorizado não encontrado para deleção."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def deletar_sistema_autorizado_endpoint(
    sistema_id: int = Path(..., description="ID do sistema autorizado a ser deletado."),
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: models.SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        db_sistema = await sistemas_autorizados_service.get_sistema_autorizado_by_id(db, sistema_id=sistema_id)
        if db_sistema is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sistema autorizado com ID {sistema_id} não encontrado para deleção.")
        
        deleted_sistema = await sistemas_autorizados_service.delete_sistema_autorizado(db, db_sistema)
        return deleted_sistema
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro de banco de dados ao deletar o sistema autorizado {sistema_id}. Tente novamente. Erro: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao deletar o sistema autorizado {sistema_id}. Tente novamente. Erro: {str(e)}"
        )

