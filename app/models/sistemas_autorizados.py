from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func # Importar func
from app.db.base_class import Base # Usar a Base correta do projeto

class SistemaAutorizado(Base):
    __tablename__ = 'sistemas_autorizados'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    ativo = Column(Boolean, default=True)
    descricao = Column(String, nullable=True)
    data_criacao = Column(DateTime, default=func.now()) # Usar func.now() para default
    ultima_atividade = Column(DateTime, nullable=True)

