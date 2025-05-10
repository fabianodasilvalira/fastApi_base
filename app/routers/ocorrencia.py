from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import models # Adicionado para type hint de User
from app.db.session import get_async_db
from app.schemas.ocorrencia_schemas import OcorrenciaOut, OcorrenciaCreate
from app.services import ocorrencia_service
from app.core.dependencies import get_current_authorized_system, require_admin_user # Adicionado require_admin_user
from app.models.sistemas_autorizados import SistemaAutorizado # Importar o modelo para type hint

# O prefixo é definido no main.py como /api/v1/ocorrencias
router = APIRouter()

@router.post("/", response_model=OcorrenciaOut, summary="Criar nova ocorrência (Admin + Sistema Autorizado)")
async def create_ocorrencia(
    ocorrencia: OcorrenciaCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user), # Adicionada autenticação de usuário admin
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system) 
):
    """
    Cria uma nova ocorrência. 
    Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.
    """
    # Se o user_id na OcorrenciaCreate for para o *criador* da ocorrência (que pode não ser o admin logado),
    # então o payload deve continuar vindo como está. Se for para registrar *quem* está fazendo a operação via API,
    # poderia ser `ocorrencia.user_id = current_user.id` ou algo similar, dependendo da lógica de negócio.
    # Por ora, assume-se que o user_id no payload é o usuário associado à ocorrência em si.
    return await ocorrencia_service.create_ocorrencia(db, ocorrencia)

@router.get("/", response_model=List[OcorrenciaOut], summary="Listar todas as ocorrências (Admin + Sistema Autorizado)")
async def read_ocorrencias(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user), # Adicionada autenticação de usuário admin
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Lista todas as ocorrências com paginação. 
    Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.
    """
    return await ocorrencia_service.get_ocorrencias(db, skip, limit)

@router.get("/{ocorrencia_id}", response_model=OcorrenciaOut, summary="Obter ocorrência por ID (Admin + Sistema Autorizado)")
async def read_ocorrencia(
    ocorrencia_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user), # Adicionada autenticação de usuário admin
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Obtém uma ocorrência específica pelo seu ID. 
    Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.
    """
    db_ocorrencia = await ocorrencia_service.get_ocorrencia_by_id(db, ocorrencia_id)
    if db_ocorrencia is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    return db_ocorrencia

@router.put("/{ocorrencia_id}", response_model=OcorrenciaOut, summary="Atualizar ocorrência por ID (Admin + Sistema Autorizado)")
async def update_ocorrencia(
    ocorrencia_id: int,
    ocorrencia_update: OcorrenciaCreate, # Usar OcorrenciaCreate para atualização por enquanto, idealmente seria um OcorrenciaUpdate
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user), # Adicionada autenticação de usuário admin
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Atualiza uma ocorrência existente. 
    Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.
    """
    db_ocorrencia = await ocorrencia_service.get_ocorrencia_by_id(db, ocorrencia_id)
    if db_ocorrencia is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada para atualização")
    
    update_data = ocorrencia_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ocorrencia, key, value)
    
    db.add(db_ocorrencia)
    await db.commit()
    await db.refresh(db_ocorrencia)
    return db_ocorrencia

@router.delete("/{ocorrencia_id}", response_model=OcorrenciaOut, summary="Deletar ocorrência por ID (Admin + Sistema Autorizado)")
async def delete_ocorrencia(
    ocorrencia_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: models.User = Depends(require_admin_user), # Adicionada autenticação de usuário admin
    authorized_system: SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Deleta uma ocorrência. 
    Requer autenticação de usuário Admin E autenticação de sistema via X-API-KEY.
    """
    db_ocorrencia = await ocorrencia_service.get_ocorrencia_by_id(db, ocorrencia_id)
    if db_ocorrencia is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada para deleção")
    
    await db.delete(db_ocorrencia)
    await db.commit()
    return db_ocorrencia

