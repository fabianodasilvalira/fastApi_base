import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.models.ocorrencia import Ocorrencia
from app.schemas.ocorrencia_schemas import OcorrenciaCreate, OcorrenciaUpdate

logger = logging.getLogger(__name__)

async def create_ocorrencia(db: AsyncSession, ocorrencia: OcorrenciaCreate) -> Ocorrencia:
    db_ocorrencia = Ocorrencia(**ocorrencia.model_dump())
    try:
        db.add(db_ocorrencia)
        await db.commit()
        await db.refresh(db_ocorrencia)
        return db_ocorrencia
    except IntegrityError as e: # Caso haja alguma constraint violada (ex: FK para user_id inexistente)
        await db.rollback()
        logger.error(f"Erro de integridade ao criar ocorrência: {e}")
        raise e # Repassar para o router tratar
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao criar ocorrência: {e}")
        raise e # Repassar para o router tratar

async def get_ocorrencias(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Ocorrencia]:
    try:
        result = await db.execute(select(Ocorrencia).offset(skip).limit(limit))
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao listar ocorrências: {e}")
        # Retornar lista vazia ou levantar exceção para o router decidir
        # Por ora, levantar para o router retornar um 500
        raise e

async def get_ocorrencia_by_id(db: AsyncSession, ocorrencia_id: int) -> Optional[Ocorrencia]:
    try:
        result = await db.execute(select(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id))
        return result.scalars().first()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao buscar ocorrência por ID {ocorrencia_id}: {e}")
        # Não levantar exceção aqui, deixar o router tratar o None e retornar 404 ou 500
        return None

async def update_ocorrencia(db: AsyncSession, db_ocorrencia: Ocorrencia, ocorrencia_in: OcorrenciaUpdate) -> Ocorrencia:
    update_data = ocorrencia_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ocorrencia, key, value)
    try:
        db.add(db_ocorrencia)
        await db.commit()
        await db.refresh(db_ocorrencia)
        return db_ocorrencia
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Erro de integridade ao atualizar ocorrência {db_ocorrencia.id}: {e}")
        raise e
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao atualizar ocorrência {db_ocorrencia.id}: {e}")
        raise e

async def delete_ocorrencia(db: AsyncSession, db_ocorrencia: Ocorrencia) -> Ocorrencia:
    try:
        await db.delete(db_ocorrencia)
        await db.commit()
        return db_ocorrencia # Retorna o objeto deletado para confirmação
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao deletar ocorrência {db_ocorrencia.id}: {e}")
        raise e

