
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List

from app import models, schemas  # Adicionado para type hint de User e schemas
from app.schemas import parecer_schemas
from app.services import parecer_service
from app.db.session import get_async_db
from app.core.dependencies import get_current_authorized_system, require_admin_user
from app.models.sistemas_autorizados import SistemaAutorizado  # Importar o modelo para type hint
from fastapi import UploadFile, File
import os
from uuid import uuid4

# O prefixo é definido no main.py como /api/v1/pareceres
router = APIRouter()


@router.post(
    "/",
    response_model=parecer_schemas.ParecerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Novo Parecer (Admin + Sistema Autorizado)",
    description="Cria um novo parecer associado a uma ocorrência. Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.",
    responses={
        status.HTTP_201_CREATED: {"description": "Parecer criado com sucesso."},
        status.HTTP_400_BAD_REQUEST: {"description": "Dados de entrada inválidos."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado (Token de usuário inválido/ausente)."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido (Usuário não é admin ou X-API-KEY inválida/ausente)."},
        status.HTTP_404_NOT_FOUND: {"description": "Recurso referenciado (ex: ocorrência ou usuário) não encontrado."},
        status.HTTP_409_CONFLICT: {
            "description": "Conflito de dados (ex: referência a ID de ocorrência/usuário inexistente)."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Entidade não processável (erro de validação nos dados)."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def criar_parecer(
        parecer: parecer_schemas.ParecerCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: models.User = Depends(require_admin_user),
        authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        # Validação adicional: verificar se ocorrencia_id e user_id existem
        ocorrencia_check = await db.get(models.Ocorrencia, parecer.ocorrencia_id)
        if not ocorrencia_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ocorrência com ID {parecer.ocorrencia_id} referenciada no parecer não foi encontrada."
            )
        user_check = await db.get(models.User, parecer.user_id)
        if not user_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuário com ID {parecer.user_id} referenciado no parecer não foi encontrado."
            )

        return await parecer_service.create_parecer(db, parecer)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Não foi possível criar o parecer devido a um conflito de dados. Verifique se a ocorrência e o usuário associados existem. Erro: {str(e.orig)}"
        )
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro de banco de dados ao criar o parecer. Tente novamente. Erro: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao criar o parecer. Tente novamente. Erro: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[parecer_schemas.ParecerOut],
    summary="Listar Todos os Pareceres (Admin + Sistema Autorizado)",
    description="Lista todos os pareceres registrados com paginação. Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.",
    responses={
        status.HTTP_200_OK: {"description": "Lista de pareceres retornada com sucesso."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def listar_pareceres(
        skip: int = Query(0, ge=0, description="Registro inicial a partir do qual os resultados serão exibidos (usado para paginação)."),
        limit: int = Query(100, ge=1, le=200, description="Número máximo de registros a retornar."),
        db: AsyncSession = Depends(get_async_db),
        current_user: models.User = Depends(require_admin_user),
        authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        return await parecer_service.get_pareceres(db, skip, limit)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro de banco de dados ao listar os pareceres. Tente novamente. Erro: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao listar os pareceres. Tente novamente. Erro: {str(e)}"
        )


@router.get(
    "/{parecer_id}",
    response_model=parecer_schemas.ParecerOut,
    summary="Obter Parecer por ID (Admin + Sistema Autorizado)",
    description="Obtém um parecer específico pelo seu ID. Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.",
    responses={
        status.HTTP_200_OK: {"description": "Parecer encontrado e retornado com sucesso."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_404_NOT_FOUND: {"description": "Parecer não encontrado."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def obter_parecer(
        parecer_id: int = Path(..., description="ID do parecer a ser buscado."),
        db: AsyncSession = Depends(get_async_db),
        current_user: models.User = Depends(require_admin_user),
        authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        db_parecer = await parecer_service.get_parecer_by_id(db, parecer_id)
        if db_parecer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Parecer com ID {parecer_id} não encontrado.")
        return db_parecer
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro de banco de dados ao buscar o parecer {parecer_id}. Tente novamente. Erro: {str(e)}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao buscar o parecer {parecer_id}. Tente novamente. Erro: {str(e)}"
        )


@router.put(
    "/{parecer_id}",
    response_model=parecer_schemas.ParecerOut,
    summary="Atualizar Parecer por ID (Admin + Sistema Autorizado)",
    description="Atualiza um parecer existente pelo seu ID. Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.",
    responses={
        status.HTTP_200_OK: {"description": "Parecer atualizado com sucesso."},
        status.HTTP_400_BAD_REQUEST: {"description": "Dados de entrada inválidos."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_404_NOT_FOUND: {
            "description": "Parecer não encontrado para atualização ou recurso referenciado (ocorrência/usuário) não existe."},
        status.HTTP_409_CONFLICT: {"description": "Conflito de dados."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Entidade não processável."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def atualizar_parecer(
        parecer_update_data: parecer_schemas.ParecerUpdate,
        parecer_id: int = Path(..., description="ID do parecer a ser atualizado."),
        db: AsyncSession = Depends(get_async_db),
        current_user: models.User = Depends(require_admin_user),
        authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    try:
        db_parecer = await parecer_service.get_parecer_by_id(db, parecer_id)
        if db_parecer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Parecer com ID {parecer_id} não encontrado para atualização.")

        # Validação adicional para FKs se forem alteradas
        if parecer_update_data.ocorrencia_id is not None and parecer_update_data.ocorrencia_id != db_parecer.ocorrencia_id:
            ocorrencia_check = await db.get(models.Ocorrencia, parecer_update_data.ocorrencia_id)
            if not ocorrencia_check:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ocorrência com ID {parecer_update_data.ocorrencia_id} referenciada no parecer não foi encontrada."
                )

        if parecer_update_data.user_id is not None and parecer_update_data.user_id != db_parecer.user_id:
            user_check = await db.get(models.User, parecer_update_data.user_id)
            if not user_check:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuário com ID {parecer_update_data.user_id} referenciado no parecer não foi encontrado."
                )

        return await parecer_service.update_parecer(db, parecer_id, parecer_update_data)

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflito de dados encontrado ao atualizar o parecer {parecer_id}. Erro: {str(e.orig)}"
        )
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro de banco de dados ao atualizar o parecer {parecer_id}. Tente novamente. Erro: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro inesperado ao atualizar o parecer {parecer_id}. Tente novamente. Erro: {str(e)}"
        )


@router.put(
    "/{parecer_id}/anexo",
    response_model=parecer_schemas.ParecerOut,
    summary="Atualizar anexo do parecer (Admin + Sistema Autorizado)",
    description="Permite fazer upload e associar um novo anexo a um parecer existente.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Anexo atualizado com sucesso."},
        status.HTTP_400_BAD_REQUEST: {"description": "Arquivo inválido."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Não autorizado."},
        status.HTTP_403_FORBIDDEN: {"description": "Proibido."},
        status.HTTP_404_NOT_FOUND: {"description": "Parecer não encontrado."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Erro interno do servidor."}
    }
)
async def atualizar_anexo_parecer(
    parecer_id: int = Path(..., description="ID do parecer que receberá o novo anexo."),
    arquivo: UploadFile = File(..., description="Arquivo a ser anexado ao parecer."),
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user),
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system),
):
    try:
        parecer = await parecer_service.get_parecer_by_id(db, parecer_id)
        if not parecer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parecer com ID {parecer_id} não encontrado."
            )

        # Gerar nome único e salvar o arquivo
        extensao = os.path.splitext(arquivo.filename)[1]
        nome_arquivo = f"{uuid4().hex}{extensao}"
        caminho_destino = os.path.join("uploads/pareceres", nome_arquivo)

        os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)
        with open(caminho_destino, "wb") as f:
            conteudo = await arquivo.read()
            f.write(conteudo)

        # Atualizar o campo de anexo
        parecer.anexo = caminho_destino
        await db.commit()
        await db.refresh(parecer)

        return parecer

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar anexo do parecer. {str(e)}"
        )