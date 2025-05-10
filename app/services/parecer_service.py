from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.parecer import Parecer
from app.schemas.parecer_schemas import ParecerCreate, ParecerUpdate # Adicionado ParecerUpdate

async def create_parecer(db: AsyncSession, parecer: ParecerCreate) -> Parecer:
    db_parecer = Parecer(**parecer.model_dump()) # Usar model_dump() para Pydantic v2
    db.add(db_parecer)
    await db.commit()
    await db.refresh(db_parecer)
    return db_parecer

async def get_pareceres(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Parecer]:
    result = await db.execute(select(Parecer).offset(skip).limit(limit))
    return result.scalars().all()

async def get_parecer_by_id(db: AsyncSession, parecer_id: int) -> Parecer | None:
    result = await db.execute(select(Parecer).where(Parecer.id == parecer_id))
    return result.scalar_one_or_none()

async def update_parecer(db: AsyncSession, parecer_id: int, parecer_update: ParecerUpdate) -> Parecer | None:
    db_parecer = await get_parecer_by_id(db, parecer_id)
    if db_parecer is None:
        return None
    
    update_data = parecer_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_parecer, key, value)
    
    db.add(db_parecer)
    await db.commit()
    await db.refresh(db_parecer)
    return db_parecer

async def delete_parecer(db: AsyncSession, parecer_id: int) -> Parecer | None:
    db_parecer = await get_parecer_by_id(db, parecer_id)
    if db_parecer is None:
        return None
    await db.delete(db_parecer)
    await db.commit()
    return db_parecer

