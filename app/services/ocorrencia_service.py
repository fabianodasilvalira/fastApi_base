from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select # Para queries assíncronas
from sqlalchemy.orm import selectinload # Para eager loading, se necessário

from app.models.ocorrencia import Ocorrencia # Importar o modelo SQLAlchemy correto
from app.schemas.ocorrencia_schemas import OcorrenciaCreate, OcorrenciaUpdate # Schemas Pydantic

class OcorrenciaService:
    async def get_ocorrencia(self, db: AsyncSession, ocorrencia_id: int) -> Ocorrencia | None:
        """Busca uma ocorrência pelo ID."""
        result = await db.execute(select(Ocorrencia).filter(Ocorrencia.id == ocorrencia_id))
        return result.scalars().first()

    async def get_ocorrencias(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[Ocorrencia]:
        """Busca uma lista de ocorrências com paginação."""
        result = await db.execute(select(Ocorrencia).offset(skip).limit(limit))
        return result.scalars().all()

    async def create_ocorrencia(
        self, db: AsyncSession, *, ocorrencia_in: OcorrenciaCreate, user_id: int # Adicionado user_id
    ) -> Ocorrencia:
        """Cria uma nova ocorrência."""
        # O modelo Ocorrencia precisa ter um campo user_id
        db_ocorrencia = Ocorrencia(**ocorrencia_in.model_dump(), user_id=user_id) 
        db.add(db_ocorrencia)
        await db.commit()
        await db.refresh(db_ocorrencia)
        return db_ocorrencia

    async def update_ocorrencia(
        self, db: AsyncSession, *, ocorrencia_db: Ocorrencia, ocorrencia_in: OcorrenciaUpdate
    ) -> Ocorrencia:
        """Atualiza uma ocorrência existente."""
        update_data = ocorrencia_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ocorrencia_db, field, value)
        db.add(ocorrencia_db) # Adiciona o objeto modificado à sessão
        await db.commit()
        await db.refresh(ocorrencia_db)
        return ocorrencia_db

    async def delete_ocorrencia(self, db: AsyncSession, *, ocorrencia_id: int) -> Ocorrencia | None:
        """Deleta uma ocorrência pelo ID."""
        db_ocorrencia = await self.get_ocorrencia(db, ocorrencia_id=ocorrencia_id)
        if db_ocorrencia:
            await db.delete(db_ocorrencia)
            await db.commit()
            return db_ocorrencia
        return None

# Instância do serviço para ser importada e usada nas rotas
ocorrencia_service = OcorrenciaService()

