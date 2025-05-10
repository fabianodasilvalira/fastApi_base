from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.ocorrencia import Ocorrencia
from app.schemas.ocorrencia_schemas import OcorrenciaCreate


async def create_ocorrencia(db: AsyncSession, ocorrencia: OcorrenciaCreate):
    db_ocorrencia = Ocorrencia(**ocorrencia.dict())
    db.add(db_ocorrencia)
    await db.commit()
    await db.refresh(db_ocorrencia)
    return db_ocorrencia

async def get_ocorrencias(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Ocorrencia).offset(skip).limit(limit))
    return result.scalars().all()

async def get_ocorrencia_by_id(db: AsyncSession, ocorrencia_id: int):
    result = await db.execute(select(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id))
    return result.scalars().first()
