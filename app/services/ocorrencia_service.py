import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload

from app import models
from app.models.ocorrencia import Ocorrencia
from app.schemas.ocorrencia_schemas import OcorrenciaCreate, OcorrenciaUpdate, OcorrenciaFilterParams

logger = logging.getLogger(__name__)


def _apply_common_filters(stmt, filters: OcorrenciaFilterParams):
    """Aplica filtros comuns a uma query SQLAlchemy de ocorrências."""
    if filters.situacao_ocorrencia_id is not None:
        stmt = stmt.filter(Ocorrencia.situacao_ocorrencia_id == filters.situacao_ocorrencia_id)
    if filters.tipo_atendimento_id is not None:
        stmt = stmt.filter(Ocorrencia.tipo_atendimento_id == filters.tipo_atendimento_id)
    if filters.programa_id is not None:
        stmt = stmt.filter(Ocorrencia.programa_id == filters.programa_id)
    if filters.tipo_ocorrencia_id is not None:
        stmt = stmt.filter(Ocorrencia.tipo_ocorrencia_id == filters.tipo_ocorrencia_id)
    if filters.regiao_id is not None:
        stmt = stmt.filter(Ocorrencia.regiao_id == filters.regiao_id)
    if filters.data_ocorrencia is not None:
        stmt = stmt.filter(Ocorrencia.data_ocorrencia == filters.data_ocorrencia)
    # O filtro 'arquivado' é tratado especificamente em cada função que o utiliza, devido ao padrão N
    return stmt


async def create_ocorrencia(db: AsyncSession, ocorrencia: OcorrenciaCreate) -> Ocorrencia:
    db_ocorrencia = Ocorrencia(**ocorrencia.model_dump())
    try:
        db.add(db_ocorrencia)
        await db.commit()
        await db.refresh(db_ocorrencia)
        return db_ocorrencia
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Erro de integridade ao criar ocorrência: {e}")
        raise e
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao criar ocorrência: {e}")
        raise e


async def get_ocorrencias(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Ocorrencia]:
    try:
        result = await db.execute(select(Ocorrencia).offset(skip).limit(limit))
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao listar ocorrências: {e}")
        # Retornar lista vazia ou levantar exceção para o router decidir
        # Por ora, levantar para o router retornar um 500
        raise e


async def get_ocorrencia_by_id(db: AsyncSession, ocorrencia_id: int) -> Ocorrencia | None:
    try:
        result = await db.execute(select(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id))
        return result.scalars().first()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao buscar ocorrência por ID {ocorrencia_id}: {e}")
        # Não levantar exceção aqui, deixar o router tratar o None e retornar 404 ou 500
        return None


async def get_ocorrencia_by_id_with_pareceres(
        db: AsyncSession,
        ocorrencia_id: int,
        filters: OcorrenciaFilterParams  # Filtros se aplicam à ocorrência principal
) -> Ocorrencia | None:
    try:
        stmt = select(Ocorrencia).options(selectinload(Ocorrencia.pareceres)).filter(Ocorrencia.id == ocorrencia_id)
        # Aplicar filtros à ocorrência principal
        stmt = _apply_common_filters(stmt, filters)
        if filters.arquivado is not None:  # Aplicar filtro de arquivado se especificado
            stmt = stmt.filter(Ocorrencia.arquivado == filters.arquivado)
        else:  # Se não especificado, aplicar padrão 'N' para esta rota específica
            stmt = stmt.filter(Ocorrencia.arquivado == 'N')

        result = await db.execute(stmt)
        return result.scalars().first()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao buscar ocorrência {ocorrencia_id} com pareceres: {e}")
        return None


from sqlalchemy.dialects import postgresql  # ou mysql, dependendo do seu banco


async def get_ocorrencias_by_user_id(
        db: AsyncSession,
        user_id: int,
        filters: OcorrenciaFilterParams,
        skip: int = 0,
        limit: int = 100
) -> list[Ocorrencia]:
    try:
        stmt = select(Ocorrencia).filter(Ocorrencia.user_id == user_id)
        stmt = _apply_common_filters(stmt, filters)

        if filters.arquivado is not None:
            stmt = stmt.filter(Ocorrencia.arquivado == filters.arquivado)

        stmt = stmt.offset(skip).limit(limit)

        # Aqui você vê a query com parâmetros reais substituídos
        compiled = stmt.compile(
            dialect=postgresql.dialect(),  # troque para mysql.dialect() se for MySQL
            compile_kwargs={"literal_binds": True}
        )

        result = await db.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Erro de banco de dados ao listar ocorrências por user_id {user_id}: {e}")
        raise


async def get_ocorrencias_by_usuario_encaminhado(
        db: AsyncSession,
        usuario_encaminhado_id: int,
        filters: OcorrenciaFilterParams,
        skip: int = 0,
        limit: int = 100
) -> list[Ocorrencia]:
    try:
        stmt = select(Ocorrencia).filter(Ocorrencia.encaminhamento_usuario_id == usuario_encaminhado_id)
        stmt = _apply_common_filters(stmt, filters)
        # Padrão 'N' para arquivado se não especificado no filtro
        arquivado_filter = filters.arquivado if filters.arquivado is not None else 'N'
        stmt = stmt.filter(Ocorrencia.arquivado == arquivado_filter)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(
            f"Erro de banco de dados ao listar ocorrências por usuario_encaminhado_id {usuario_encaminhado_id}: {e}")
        raise e


async def get_ocorrencias_by_orgao_encaminhado(
        db: AsyncSession,
        orgao_encaminhado_id: int,
        filters: OcorrenciaFilterParams,
        skip: int = 0,
        limit: int = 100
) -> list[Ocorrencia]:
    try:
        stmt = select(Ocorrencia).filter(Ocorrencia.encaminhamento_orgao_id == orgao_encaminhado_id)
        stmt = _apply_common_filters(stmt, filters)
        # Padrão 'N' para arquivado se não especificado no filtro
        arquivado_filter = filters.arquivado if filters.arquivado is not None else 'N'
        stmt = stmt.filter(Ocorrencia.arquivado == arquivado_filter)

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(
            f"Erro de banco de dados ao listar ocorrências por orgao_encaminhado_id {orgao_encaminhado_id}: {e}")
        raise e


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
        return db_ocorrencia  # Retorna o objeto deletado para confirmação
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Erro de banco de dados ao deletar ocorrência {db_ocorrencia.id}: {e}")
        raise e
