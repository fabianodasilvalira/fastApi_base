import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timezone # Import timezone

from app.models.sistemas_autorizados import SistemaAutorizado
from app.schemas.sistemas_autorizados_schemas import SistemaAutorizadoCreate, SistemaAutorizadoUpdate

logger = logging.getLogger(__name__)

def gerar_token_unico():
    return str(uuid.uuid4())

async def criar_sistema_autorizado(db: AsyncSession, sistema: SistemaAutorizadoCreate) -> SistemaAutorizado:
    token_gerado = gerar_token_unico()
    
    db_sistema = SistemaAutorizado(
        nome=sistema.nome,
        descricao=sistema.descricao,
        token=token_gerado,
        ativo=sistema.ativo if sistema.ativo is not None else True,
    )
    try:
        db.add(db_sistema)
        await db.commit()
        await db.refresh(db_sistema)
        return db_sistema
    except IntegrityError as e: # Ex: nome do sistema duplicado se houver constraint unique
        await db.rollback()
        logger.error(f"Erro de integridade ao criar sistema autorizado: {e}. Detalhes: {e.orig}")
        raise e # Repassar para o router tratar
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao criar sistema autorizado: {e}")
        raise e # Repassar para o router tratar

async def get_sistemas_autorizados(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[SistemaAutorizado]:
    try:
        result = await db.execute(select(SistemaAutorizado).offset(skip).limit(limit))
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao listar sistemas autorizados: {e}")
        raise e # Levantar para o router retornar um 500

async def get_sistema_autorizado_by_id(db: AsyncSession, sistema_id: int) -> Optional[SistemaAutorizado]:
    try:
        result = await db.execute(select(SistemaAutorizado).where(SistemaAutorizado.id == sistema_id))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao buscar sistema autorizado por ID {sistema_id}: {e}")
        return None # Deixar o router tratar o None (404) ou a exceção (500)

async def get_sistema_autorizado_by_token(db: AsyncSession, token: str) -> Optional[SistemaAutorizado]:
    try:
        result = await db.execute(select(SistemaAutorizado).where(SistemaAutorizado.token == token))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao buscar sistema autorizado por token: {e}")
        return None

async def validar_token_sistema(db: AsyncSession, token: str) -> Optional[SistemaAutorizado]:
    try:
        sistema = await get_sistema_autorizado_by_token(db, token)
        if sistema and sistema.ativo:
            await atualizar_ultima_atividade_sistema(db, sistema.id) # Tenta atualizar, mas não falha a validação se isso falhar
            return sistema
        return None
    except SQLAlchemyError as e: # Erro no get_sistema_autorizado_by_token ou atualizar_ultima_atividade_sistema
        logger.error(f"Erro de banco de dados durante a validação do token do sistema: {e}")
        # Neste caso, é mais seguro considerar o token inválido ou inacessível
        return None 

async def atualizar_ultima_atividade_sistema(db: AsyncSession, sistema_id: int) -> Optional[SistemaAutorizado]:
    try:
        sistema = await get_sistema_autorizado_by_id(db, sistema_id)
        if sistema:
            sistema.ultima_atividade = datetime.now(timezone.utc) # Usar timezone.utc
            db.add(sistema)
            await db.commit()
            await db.refresh(sistema)
            return sistema
        return None # Sistema não encontrado
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao atualizar última atividade do sistema {sistema_id}: {e}")
        # Não levantar exceção aqui para não quebrar a validação de token se for chamado de lá
        # O chamador (validar_token_sistema) já trata erros de DB.
        # Se chamado diretamente por um endpoint, o endpoint deve tratar o None.
        return None 

async def update_sistema_autorizado(db: AsyncSession, db_sistema: SistemaAutorizado, sistema_update: SistemaAutorizadoUpdate) -> SistemaAutorizado:
    update_data = sistema_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sistema, key, value)
    try:
        db.add(db_sistema)
        await db.commit()
        await db.refresh(db_sistema)
        return db_sistema
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Erro de integridade ao atualizar sistema autorizado {db_sistema.id}: {e}. Detalhes: {e.orig}")
        raise e
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao atualizar sistema autorizado {db_sistema.id}: {e}")
        raise e

async def delete_sistema_autorizado(db: AsyncSession, db_sistema: SistemaAutorizado) -> SistemaAutorizado:
    try:
        await db.delete(db_sistema)
        await db.commit()
        return db_sistema
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao deletar sistema autorizado {db_sistema.id}: {e}")
        raise e

