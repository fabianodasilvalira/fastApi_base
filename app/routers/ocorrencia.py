from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.schemas.ocorrencia_schemas import OcorrenciaOut, OcorrenciaCreate
from app.services import ocorrencia_service

router = APIRouter(prefix="/ocorrencias", tags=["Ocorrências"])

@router.post("/", response_model=OcorrenciaOut)
async def create_ocorrencia(
    ocorrencia: OcorrenciaCreate,
    db: AsyncSession = Depends(get_async_db)
):
    return await ocorrencia_service.create_ocorrencia(db, ocorrencia)

@router.get("/", response_model=list[OcorrenciaOut])
async def read_ocorrencias(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
):
    return await ocorrencia_service.get_ocorrencias(db, skip, limit)

@router.get("/{ocorrencia_id}", response_model=OcorrenciaOut)
async def read_ocorrencia(
    ocorrencia_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    db_ocorrencia = await ocorrencia_service.get_ocorrencia_by_id(db, ocorrencia_id)
    if db_ocorrencia is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada")
    return db_ocorrencia
