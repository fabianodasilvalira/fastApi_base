from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime

class OcorrenciaBase(BaseModel):
    data_ocorrencia: Optional[date]
    hora_ocorrencia: Optional[time]
    situacao_ocorrencia_id: Optional[int]
    tipo_atendimento_id: Optional[int]
    programa_id: Optional[int]
    tipo_ocorrencia_id: Optional[int]
    protocolo: Optional[str]
    regiao_id: Optional[int]
    sigilo: Optional[str]
    nome_completo: Optional[str]
    endereco: Optional[str]
    fone1: Optional[str]
    fone2: Optional[str]
    email: Optional[str]
    url_file: Optional[str]
    assunto: Optional[str]
    mensagem: Optional[str]
    encaminhamento_orgao_id: Optional[int]
    encaminhamento_usuario_id: Optional[int]
    encaminhamento_data: Optional[datetime]
    parecer_usuario_id: Optional[int]
    parecer_descricao: Optional[str]
    parecer_data: Optional[datetime]
    notificar: Optional[str]
    notificado: Optional[str]
    situacao_anterior: Optional[int]
    programa_anterior: Optional[int]
    tipo_atend_anterior: Optional[int]
    pessoa_id: Optional[int]
    user_id: Optional[int]
    cadastro: Optional[datetime]
    atualizacao: Optional[datetime]
    latitude: Optional[float]
    longitude: Optional[float]
    arquivado: Optional[str]

class OcorrenciaCreate(OcorrenciaBase):
    pass

class OcorrenciaOut(OcorrenciaBase):
    id: int

    class Config:
        orm_mode = True
