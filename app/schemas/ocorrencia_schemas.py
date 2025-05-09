from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, time, datetime

class OcorrenciaBase(BaseModel):
    data_ocorrencia: date
    hora_ocorrencia: time
    situacao_ocorrencia_id: int
    tipo_atendimento_id: int
    programa_id: int
    tipo_ocorrencia_id: int
    protocolo: str
    regiao_id: int
    sigilo: str
    nome_completo: str
    endereco: str
    fone1: str
    fone2: str
    email: EmailStr
    url_file: Optional[str] = None
    assunto: Optional[str] = ''
    mensagem: str
    encaminhamento_orgao_id: int
    encaminhamento_usuario_id: Optional[int]
    encaminhamento_data: Optional[datetime]
    parecer_usuario_id: int
    parecer_descricao: str
    parecer_data: Optional[datetime]
    notificar: str
    notificado: str
    situacao_anterior: int
    programa_anterior: int
    tipo_atend_anterior: int
    pessoa_id: Optional[int]
    user_id: Optional[int]
    cadastro: datetime
    atualizacao: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    arquivado: str

class OcorrenciaCreate(OcorrenciaBase):
    pass

class OcorrenciaOut(OcorrenciaBase):
    id: int

    class Config:
        orm_mode = True
