# app/schemas/ocorrencia_schemas.py
from typing import Optional
from datetime import date, time, datetime
from pydantic import BaseModel

class OcorrenciaBase(BaseModel):
    data_ocorrencia: Optional[date] = None
    hora_ocorrencia: Optional[time] = None
    situacao_ocorrencia_id: Optional[int] = None
    tipo_atendimento_id: Optional[int] = None
    programa_id: Optional[int] = None
    tipo_ocorrencia_id: Optional[int] = None
    protocolo: Optional[str] = None
    regiao_id: Optional[int] = None
    sigilo: Optional[str] = None
    nome_completo: Optional[str] = None
    endereco: Optional[str] = None
    fone1: Optional[str] = None
    fone2: Optional[str] = None
    email: Optional[str] = None
    url_file: Optional[str] = None
    assunto: Optional[str] = None
    mensagem: Optional[str] = None
    encaminhamento_orgao_id: Optional[int] = None
    encaminhamento_usuario_id: Optional[int] = None
    encaminhamento_data: Optional[datetime] = None # Adicionado conforme modelo
    parecer_usuario_id: Optional[int] = None
    parecer_descricao: Optional[str] = None
    parecer_data: Optional[datetime] = None # Adicionado conforme modelo
    notificar: Optional[str] = None
    notificado: Optional[str] = None
    situacao_anterior: Optional[int] = None
    programa_anterior: Optional[int] = None
    tipo_atend_anterior: Optional[int] = None
    pessoa_id: Optional[int] = None
    user_id: Optional[int] = None
    cadastro: Optional[datetime] = None
    atualizacao: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    arquivado: Optional[str] = None

class OcorrenciaCreate(OcorrenciaBase):
    # Campos obrigatórios para criação podem ser definidos aqui, se diferentes de OcorrenciaBase
    pass

class OcorrenciaUpdate(OcorrenciaBase):
    # Todos os campos são opcionais para atualização, herdando de OcorrenciaBase
    # onde todos já são Optional.
    pass

class OcorrenciaOut(OcorrenciaBase):
    id: int

    class Config:
        from_attributes = True # Alterado de orm_mode para Pydantic V2

