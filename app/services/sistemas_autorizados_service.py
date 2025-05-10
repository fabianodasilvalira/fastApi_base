import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from datetime import datetime

from app.models.sistemas_autorizados import SistemaAutorizado # Corrigir import se o nome do arquivo/modelo for diferente
from app.schemas.sistemas_autorizados_schemas import SistemaAutorizadoCreate, SistemaAutorizadoUpdate # Corrigir import

def gerar_token_unico():
    return str(uuid.uuid4())

async def criar_sistema_autorizado(db: AsyncSession, sistema: SistemaAutorizadoCreate) -> SistemaAutorizado:
    token_gerado = gerar_token_unico()
    # Verificar se o token já existe (embora a chance seja mínima com UUID4)
    # result = await db.execute(select(SistemaAutorizado).where(SistemaAutorizado.token == token_gerado))
    # while result.scalar_one_or_none() is not None:
    #     token_gerado = gerar_token_unico()
    #     result = await db.execute(select(SistemaAutorizado).where(SistemaAutorizado.token == token_gerado))

    db_sistema = SistemaAutorizado(
        nome=sistema.nome,
        descricao=sistema.descricao,
        token=token_gerado, # Usar o token gerado
        ativo=sistema.ativo if sistema.ativo is not None else True,
        # data_criacao é default no modelo
    )
    db.add(db_sistema)
    await db.commit()
    await db.refresh(db_sistema)
    return db_sistema

async def get_sistemas_autorizados(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[SistemaAutorizado]:
    result = await db.execute(select(SistemaAutorizado).offset(skip).limit(limit))
    return result.scalars().all()

async def get_sistema_autorizado_by_id(db: AsyncSession, sistema_id: int) -> SistemaAutorizado | None:
    result = await db.execute(select(SistemaAutorizado).where(SistemaAutorizado.id == sistema_id))
    return result.scalar_one_or_none()

async def get_sistema_autorizado_by_token(db: AsyncSession, token: str) -> SistemaAutorizado | None:
    result = await db.execute(select(SistemaAutorizado).where(SistemaAutorizado.token == token))
    return result.scalar_one_or_none()

async def validar_token_sistema(db: AsyncSession, token: str) -> SistemaAutorizado | None:
    sistema = await get_sistema_autorizado_by_token(db, token)
    if sistema and sistema.ativo:
        # Atualizar ultima_atividade ao validar o token com sucesso
        await atualizar_ultima_atividade_sistema(db, sistema.id)
        return sistema
    return None

async def atualizar_ultima_atividade_sistema(db: AsyncSession, sistema_id: int) -> SistemaAutorizado | None:
    sistema = await get_sistema_autorizado_by_id(db, sistema_id)
    if sistema:
        sistema.ultima_atividade = datetime.utcnow() # Usar utcnow para consistência
        db.add(sistema)
        await db.commit()
        await db.refresh(sistema)
        return sistema
    return None

async def update_sistema_autorizado(db: AsyncSession, sistema_id: int, sistema_update: SistemaAutorizadoUpdate) -> SistemaAutorizado | None:
    db_sistema = await get_sistema_autorizado_by_id(db, sistema_id)
    if db_sistema is None:
        return None
    
    update_data = sistema_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sistema, key, value)
    
    db.add(db_sistema)
    await db.commit()
    await db.refresh(db_sistema)
    return db_sistema

async def delete_sistema_autorizado(db: AsyncSession, sistema_id: int) -> SistemaAutorizado | None:
    db_sistema = await get_sistema_autorizado_by_id(db, sistema_id)
    if db_sistema is None:
        return None
    await db.delete(db_sistema)
    await db.commit()
    return db_sistema

