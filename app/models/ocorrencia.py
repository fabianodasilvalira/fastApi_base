from datetime import date, datetime

from sqlalchemy import Column, Integer, String, Date, Time, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.orm import relationship # Adicionar relationship

from app.db.base_class import Base # Corrigido para usar a Base correta do projeto


class Ocorrencia(Base):
    __tablename__ = "ocorrencia"

    id = Column(Integer, primary_key=True, index=True)
    data_ocorrencia = Column(Date, default=date.today, nullable=True)
    hora_ocorrencia = Column(Time, default=lambda: datetime.now().time(), nullable=True)

    situacao_ocorrencia_id = Column(Integer, nullable=False)
    tipo_atendimento_id = Column(Integer, nullable=True)
    programa_id = Column(Integer, nullable=False)
    tipo_ocorrencia_id = Column(Integer, nullable=True)
    protocolo = Column(String(20), nullable=True)
    regiao_id = Column(Integer, nullable=False)
    sigilo = Column(String(1), nullable=True)
    nome_completo = Column(String(150), nullable=True)
    endereco = Column(String(255), nullable=True)
    fone1 = Column(String(15), nullable=True)
    fone2 = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)
    url_file = Column(Text, nullable=True)
    assunto = Column(String(255), nullable=False)
    mensagem = Column(Text, nullable=False)
    encaminhamento_orgao_id = Column(Integer, nullable=True)
    encaminhamento_usuario_id = Column(Integer, nullable=True)
    encaminhamento_data = Column(DateTime, nullable=True)
    parecer_usuario_id = Column(Integer, nullable=True)
    parecer_descricao = Column(Text, nullable=True)
    parecer_data = Column(DateTime, nullable=True)
    notificar = Column(String(1), nullable=True)
    notificado = Column(String(1), nullable=True)
    situacao_anterior = Column(Integer, nullable=True)
    programa_anterior = Column(Integer, nullable=True)
    tipo_atend_anterior = Column(Integer, nullable=True)
    pessoa_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=False)
    cadastro = Column(DateTime, nullable=True)
    atualizacao = Column(DateTime, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    arquivado = Column(String(1), nullable=True, default="N")

    # Relacionamento com Parecer
    pareceres = relationship("Parecer", back_populates="ocorrencia")
