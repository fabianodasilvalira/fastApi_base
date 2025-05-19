# app/models/tipo_ocorrencia.py
from sqlalchemy import Column, Integer, String, DateTime, CHAR
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class TipoOcorrencia(Base):
    __tablename__ = "tipo_ocorrencia"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    icon = Column(String(255), nullable=True)
    ativo = Column(CHAR(1), nullable=False, default='S')
    cadastro = Column(DateTime, nullable=True)
    atualizacao = Column(DateTime, nullable=True)

    ocorrencias = relationship("Ocorrencia", back_populates="tipo_ocorrencia")
