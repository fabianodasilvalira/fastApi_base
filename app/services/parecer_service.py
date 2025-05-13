import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.models.parecer import Parecer
from app.schemas.parecer_schemas import ParecerCreate, ParecerUpdate

logger = logging.getLogger(__name__)

async def create_parecer(db: AsyncSession, parecer: ParecerCreate) -> Parecer:
    db_parecer = Parecer(**parecer.model_dump())
    try:
        db.add(db_parecer)
        await db.commit()
        await db.refresh(db_parecer)
        return db_parecer
    except IntegrityError as e: # Ex: FK para ocorrencia_id ou user_id inexistente
        await db.rollback()
        logger.error(f"Erro de integridade ao criar parecer: {e}. Detalhes: {e.orig}")
        raise e # Repassar para o router tratar como 409 ou 422
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao criar parecer: {e}")
        raise e # Repassar para o router tratar como 500

async def get_pareceres(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Parecer]:
    try:
        result = await db.execute(select(Parecer).offset(skip).limit(limit))
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao listar pareceres: {e}")
        raise e # Levantar para o router retornar um 500

async def get_parecer_by_id(db: AsyncSession, parecer_id: int) -> Optional[Parecer]:
    try:
        result = await db.execute(select(Parecer).where(Parecer.id == parecer_id))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao buscar parecer por ID {parecer_id}: {e}")
        # Deixar o router tratar o None (404) ou a exceção (500)
        # Se o erro for crítico, levantar a exceção pode ser melhor.
        # Por ora, retornando None para consistência com outros getters que não levantam em erro de DB.
        return None

async def update_parecer(db: AsyncSession, db_parecer: Parecer, parecer_update: ParecerUpdate) -> Parecer:
    update_data = parecer_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_parecer, key, value)
    try:
        db.add(db_parecer)
        await db.commit()
        await db.refresh(db_parecer)
        return db_parecer
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Erro de integridade ao atualizar parecer {db_parecer.id}: {e}. Detalhes: {e.orig}")
        raise e
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao atualizar parecer {db_parecer.id}: {e}")
        raise e

async def delete_parecer(db: AsyncSession, db_parecer: Parecer) -> Parecer:
    # O parecer já foi buscado e confirmado como existente pelo router antes de chamar este service.
    try:
        await db.delete(db_parecer)
        await db.commit()
        return db_parecer # Retorna o objeto deletado para confirmação
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao deletar parecer {db_parecer.id}: {e}")
        raise e

