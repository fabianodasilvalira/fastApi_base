from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app import models, schemas # Import models for type hinting
from app.services import sistemas_autorizados_service
from app.db.session import get_async_db
from app.core.dependencies import get_current_authorized_system, require_admin_user # Import dependencies

# O prefixo é definido no main.py como /api/v1/sistemas-autorizados
router = APIRouter()

@router.post("/", 
    response_model=schemas.SistemaAutorizadoComTokenResponse, 
    summary="Criar novo sistema autorizado (Admin)",
    status_code=status.HTTP_201_CREATED
)
async def criar_sistema_autorizado_endpoint(
    sistema: schemas.SistemaAutorizadoCreate, 
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user) # Apenas Admin pode criar sistemas
):
    """
    Registra um novo sistema cliente e gera um token de API para ele.
    **Requer autenticação de usuário Admin.**
    """
    db_sistema = await sistemas_autorizados_service.criar_sistema_autorizado(db=db, sistema=sistema)
    return db_sistema

@router.get("/", 
    response_model=List[schemas.SistemaAutorizadoResponse], 
    summary="Listar sistemas autorizados (Admin + Sistema Autorizado)"
)
async def listar_sistemas_autorizados_endpoint(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user), # Requer Admin
    authorized_system: models.SistemaAutorizado = Depends(get_current_authorized_system) # Requer X-API-KEY
):
    """
    Lista os sistemas clientes registrados (não expõe os tokens).
    **Requer autenticação de usuário Admin E X-API-KEY de sistema autorizado.**
    """
    sistemas = await sistemas_autorizados_service.get_sistemas_autorizados(db, skip=skip, limit=limit)
    return sistemas

@router.get("/{sistema_id}", 
    response_model=schemas.SistemaAutorizadoResponse, 
    summary="Obter sistema autorizado por ID (Admin + Sistema Autorizado)"
)
async def obter_sistema_autorizado_endpoint(
    sistema_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: models.SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Obtém dados de um sistema autorizado específico pelo ID.
    **Requer autenticação de usuário Admin E X-API-KEY de sistema autorizado.**
    """
    db_sistema = await sistemas_autorizados_service.get_sistema_autorizado_by_id(db, sistema_id=sistema_id)
    if db_sistema is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sistema autorizado não encontrado")
    return db_sistema

@router.post("/validar-token/", 
    response_model=schemas.SistemaAutorizadoResponse, 
    summary="Validar token de sistema (Sistema Autorizado)"
)
async def validar_token_endpoint(
    # O token é obtido de X-API-KEY pela dependência get_current_authorized_system
    # Não precisa ser passado explicitamente como parâmetro aqui se a dependência já o extrai.
    # Se a dependência get_current_authorized_system já usa Header("X-API-KEY"), então só precisamos dela.
    # token_payload: str = Header(..., alias="X-API-KEY", description="Token de API do sistema cliente"), 
    db: AsyncSession = Depends(get_async_db),
    # Esta rota é para um sistema validar seu próprio token (ou outro), então só precisa do X-API-KEY
    validating_system: models.SistemaAutorizado = Depends(get_current_authorized_system) 
):
    """
    Valida um token de API de sistema cliente (X-API-KEY fornecido no header).
    Se válido e ativo, retorna os dados do sistema e atualiza sua última atividade.
    **Requer X-API-KEY de sistema autorizado.**
    """
    # A dependência get_current_authorized_system já valida e retorna o sistema.
    # Se chegou aqui, o token é válido.
    return validating_system

@router.put("/{sistema_id}/ultima-atividade/", 
    response_model=schemas.SistemaAutorizadoResponse, 
    summary="Atualizar última atividade do sistema (Admin + Sistema Autorizado)"
)
async def atualizar_ultima_atividade_endpoint(
    sistema_id: int, 
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user), # Ou apenas sistema autorizado, dependendo da lógica de negócio
    authorized_system: models.SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Atualiza o campo 'ultima_atividade' de um sistema cliente específico.
    **Requer autenticação de usuário Admin E X-API-KEY de sistema autorizado.**
    """
    sistema_atualizado = await sistemas_autorizados_service.atualizar_ultima_atividade_sistema(db, sistema_id=sistema_id)
    if sistema_atualizado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sistema não encontrado para atualizar última atividade.")
    return sistema_atualizado

@router.put("/{sistema_id}", 
    response_model=schemas.SistemaAutorizadoResponse, 
    summary="Atualizar sistema autorizado (Admin + Sistema Autorizado)"
)
async def atualizar_sistema_autorizado_endpoint(
    sistema_id: int,
    sistema_update: schemas.SistemaAutorizadoUpdate,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: models.SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Atualiza dados de um sistema autorizado.
    **Requer autenticação de usuário Admin E X-API-KEY de sistema autorizado.**
    """
    db_sistema = await sistemas_autorizados_service.update_sistema_autorizado(db, sistema_id=sistema_id, sistema_update=sistema_update)
    if db_sistema is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sistema autorizado não encontrado para atualização")
    return db_sistema

@router.delete("/{sistema_id}", 
    response_model=schemas.SistemaAutorizadoResponse, 
    summary="Deletar sistema autorizado (Admin + Sistema Autorizado)"
)
async def deletar_sistema_autorizado_endpoint(
    sistema_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.User = Depends(require_admin_user),
    authorized_system: models.SistemaAutorizado = Depends(get_current_authorized_system)
):
    """
    Deleta um sistema autorizado.
    **Requer autenticação de usuário Admin E X-API-KEY de sistema autorizado.**
    """
    db_sistema = await sistemas_autorizados_service.delete_sistema_autorizado(db, sistema_id=sistema_id)
    if db_sistema is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sistema autorizado não encontrado para deleção")
    return db_sistema

