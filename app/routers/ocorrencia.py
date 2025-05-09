from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession # Importar AsyncSession
from typing import List

from app import schemas, services # Mantido
from app.core.dependencies import get_db, get_current_active_user # Importar dependências corretas
from app.models.user import User # Importar modelo User para tipagem de current_user

router = APIRouter(
    prefix="/ocorrencias", 
    tags=["Ocorrências"],
    dependencies=[Depends(get_current_active_user)] # Aplicar autenticação a todas as rotas deste router
)

@router.post("/", response_model=schemas.OcorrenciaOut)
async def create_ocorrencia_route(
    ocorrencia: schemas.OcorrenciaCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Usuário autenticado
):
    # Aqui você pode passar current_user.id para o serviço se precisar registrar o criador
    return await services.ocorrencia_service.create_ocorrencia(db=db, ocorrencia_in=ocorrencia, user_id=current_user.id)

@router.get("/", response_model=List[schemas.OcorrenciaOut])
async def read_ocorrencias_route(
    skip: int = 0, 
    limit: int = 100, # Aumentado o limite padrão, pode ser ajustado
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Usuário autenticado
):
    ocorrencias = await services.ocorrencia_service.get_ocorrencias(db, skip=skip, limit=limit)
    return ocorrencias

@router.get("/{ocorrencia_id}", response_model=schemas.OcorrenciaOut)
async def read_ocorrencia_route(
    ocorrencia_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Usuário autenticado
):
    db_ocorrencia = await services.ocorrencia_service.get_ocorrencia(db, ocorrencia_id=ocorrencia_id)
    if db_ocorrencia is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    # Adicionar verificação se o usuário tem permissão para ver esta ocorrência específica, se necessário
    return db_ocorrencia

@router.put("/{ocorrencia_id}", response_model=schemas.OcorrenciaOut)
async def update_ocorrencia_route(
    ocorrencia_id: int, 
    ocorrencia: schemas.OcorrenciaUpdate, # Usar OcorrenciaUpdate para PUT
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Usuário autenticado
):
    db_ocorrencia = await services.ocorrencia_service.get_ocorrencia(db, ocorrencia_id=ocorrencia_id)
    if db_ocorrencia is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    # Adicionar verificação se o usuário tem permissão para atualizar esta ocorrência, se necessário
    # Por exemplo, verificar se current_user.id == db_ocorrencia.user_id ou se é admin
    return await services.ocorrencia_service.update_ocorrencia(db=db, ocorrencia_db=db_ocorrencia, ocorrencia_in=ocorrencia)

@router.delete("/{ocorrencia_id}", response_model=schemas.OcorrenciaOut) # Manter response_model para consistência ou retornar status
async def delete_ocorrencia_route(
    ocorrencia_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Usuário autenticado
):
    db_ocorrencia = await services.ocorrencia_service.get_ocorrencia(db, ocorrencia_id=ocorrencia_id)
    if db_ocorrencia is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    # Adicionar verificação se o usuário tem permissão para deletar esta ocorrência, se necessário
    deleted_ocorrencia = await services.ocorrencia_service.delete_ocorrencia(db=db, ocorrencia_id=ocorrencia_id)
    if not deleted_ocorrencia:
         # Caso o serviço retorne None ou False em falha de deleção não coberta pelo get_ocorrencia
        raise HTTPException(status_code=500, detail="Não foi possível deletar a ocorrência")
    return deleted_ocorrencia # Retorna a ocorrência deletada conforme o response_model

