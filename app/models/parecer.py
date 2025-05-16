from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base # Garante que está usando a Base correta do projeto

class Parecer(Base):
    __tablename__ = "parecer"

    id = Column(Integer, primary_key=True, index=True)
    ocorrencia_id = Column(Integer, ForeignKey("ocorrencia.id")) # Mantém o nome da tabela 'ocorrencia' como no model original
    situacao_ocorrencia_id = Column(Integer, nullable=True)
    parecer_publico = Column(Text, nullable=True)
    parecer_privado = Column(Text, nullable=True)
    parecer_data = Column(DateTime, default=datetime.utcnow)
    parecer_usuario_id = Column(Integer, nullable=True)
    encam_orgao_id = Column(Integer, nullable=True)
    encam_usuario_id = Column(Integer, nullable=True)
    url_file = Column(Text, nullable=True)
    cadastro = Column(DateTime, default=datetime.utcnow)
    atualizacao = Column(DateTime, nullable=True)
    reg_atualizado = Column(String(1), default="S")

    # Relacionamento com Ocorrencia
    # O nome da tabela para Ocorrencia é 'ocorrencia' (singular) conforme o model original, não 'ocorrencias'
    ocorrencia = relationship("Ocorrencia", back_populates="pareceres")

