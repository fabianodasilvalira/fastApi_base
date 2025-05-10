from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import models # Adicionado para type hint de User
from app.schemas import parecer_schemas as schemas
from app.services import parecer_service
from app.db.session import get_async_db
from app.core.dependencies import get_current_authorized_system, require_admin_user # Adicionado require_admin_user
from app.models.sistemas_autorizados import SistemaAutorizado # Importar o modelo para type hint

# O prefixo é definido no main.py como /api/v1/pareceres
router = APIRouter()

@router.post("/", response_model=schemas.ParecerOut, summary="Criar novo parecer (Admin + Sistema Autorizado)")
async def create_parecer(
    parecer: schemas.ParecerCreate, 
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user), # Adicionada autenticação de usuário admin
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Cria um novo parecer associado a uma ocorrência. 
    Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.
    """
    # Adicionar o user_id do admin logado ao parecer, se o schema/service precisar
    # parecer_data = parecer.model_dump()
    # parecer_data["user_id"] = current_user.id # Exemplo, ajustar conforme o schema ParecerCreate
    return await parecer_service.create_parecer(db, parecer)

@router.get("/", response_model=List[schemas.ParecerOut], summary="Listar todos os pareceres (Admin + Sistema Autorizado)")
async def read_pareceres(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user), # Adicionada autenticação de usuário admin
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Lista todos os pareceres com paginação. 
    Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.
    """
    return await parecer_service.get_pareceres(db, skip, limit)

@router.get("/{parecer_id}", response_model=schemas.ParecerOut, summary="Obter parecer por ID (Admin + Sistema Autorizado)")
async def read_parecer(
    parecer_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user), # Adicionada autenticação de usuário admin
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Obtém um parecer específico pelo seu ID. 
    Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.
    """
    db_parecer = await parecer_service.get_parecer_by_id(db, parecer_id)
    if db_parecer is None:
        raise HTTPException(status_code=404, detail="Parecer não encontrado")
    return db_parecer

@router.put("/{parecer_id}", response_model=schemas.ParecerOut, summary="Atualizar parecer por ID (Admin + Sistema Autorizado)")
async def update_parecer_endpoint(
    parecer_id: int, 
    parecer: schemas.ParecerUpdate, 
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user), # Adicionada autenticação de usuário admin
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Atualiza um parecer existente pelo seu ID. 
    Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.
    """
    db_parecer_updated = await parecer_service.update_parecer(db, parecer_id, parecer)
    if db_parecer_updated is None:
        raise HTTPException(status_code=404, detail="Parecer não encontrado para atualização")
    return db_parecer_updated

@router.delete("/{parecer_id}", response_model=schemas.ParecerOut, summary="Deletar parecer por ID (Admin + Sistema Autorizado)")
async def delete_parecer_endpoint(
    parecer_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user), # Adicionada autenticação de usuário admin
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Deleta um parecer pelo seu ID. 
    Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.
    """
    db_parecer_deleted = await parecer_service.delete_parecer(db, parecer_id)
    if db_parecer_deleted is None:
        raise HTTPException(status_code=404, detail="Parecer não encontrado para deleção")
    return db_parecer_deleted

