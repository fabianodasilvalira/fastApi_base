from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func # Importar func
from app.db.base_class import Base # Usar a Base correta do projeto

class SistemaAutorizado(Base):
    __tablename__ = 'sistemas_autorizados'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), index=True, nullable=False)  # ✅ TAMANHO DEFINIDO
    token = Column(String(255), unique=True, index=True, nullable=False)
    ativo = Column(Boolean, default=True)
    descricao = Column(String(500), nullable=True)  # opcional: definir tamanho aqui também
    data_criacao = Column(DateTime, default=func.now())
    ultima_atividade = Column(DateTime, nullable=True)


