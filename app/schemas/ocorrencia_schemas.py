from typing import Optional, List
from datetime import date, time, datetime

from fastapi import Query
from pydantic import BaseModel, Field, constr

from .parecer_schemas import ParecerOut


class OcorrenciaBase(BaseModel):
    data_ocorrencia: Optional[date] = None
    hora_ocorrencia: Optional[time] = None
    situacao_ocorrencia_id: Optional[int] = None
    tipo_atendimento_id: Optional[int] = None
    programa_id: int
    tipo_ocorrencia_id: int
    protocolo: Optional[str] = None
    regiao_id: int
    sigilo: Optional[str] = Field(None, max_length=1)
    nome_completo: Optional[str] = Field(None, max_length=150)
    endereco: Optional[str] = Field(None, max_length=255)
    fone1: Optional[str] = Field(None, max_length=15)
    fone2: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    url_file: Optional[constr(max_length=2000)] = None
    assunto: str
    mensagem: str
    encaminhamento_orgao_id: Optional[int] = None
    encaminhamento_usuario_id: Optional[int] = None
    encaminhamento_data: Optional[datetime] = None
    parecer_usuario_id: Optional[int] = None
    parecer_descricao: Optional[str] = None
    parecer_data: Optional[datetime] = None
    notificar: Optional[str] = Field(None, max_length=1)
    notificado: Optional[str] = Field(None, max_length=1)
    situacao_anterior: Optional[int] = None
    programa_anterior: Optional[int] = None
    tipo_atend_anterior: Optional[int] = None
    pessoa_id: Optional[int] = None
    user_id: int
    cadastro: Optional[datetime] = None
    atualizacao: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    arquivado: Optional[str] = Field(None, max_length=1)


class OcorrenciaCreate(BaseModel):
    tipo_ocorrencia_id: int
    assunto: str
    mensagem: str

    protocolo: Optional[str] = None
    sigilo: Optional[str] = "N"
    endereco: Optional[str] = None
    fone2: Optional[str] = None
    url_file: Optional[constr(max_length=2000)] = None
    encaminhamento_orgao_id: Optional[int] = None
    encaminhamento_usuario_id: Optional[int] = None
    encaminhamento_data: Optional[datetime] = None
    parecer_usuario_id: Optional[int] = None
    parecer_descricao: Optional[str] = None
    parecer_data: Optional[datetime] = None
    notificar: Optional[str]  = None
    notificado: Optional[str] = "N"
    pessoa_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class OcorrenciaUpdate(OcorrenciaBase):
    pass


class OcorrenciaOut(OcorrenciaBase):
    id: int

    class Config:
        from_attributes = True


class OcorrenciaFilterParams(BaseModel):
    situacao_ocorrencia_id: Optional[int] = Query(None, description="Filtrar por ID da situação da ocorrência")
    tipo_atendimento_id: Optional[int] = Query(None, description="Filtrar por ID do tipo de atendimento")
    programa_id: Optional[int] = Query(None, description="Filtrar por ID do programa")
    tipo_ocorrencia_id: Optional[int] = Query(None, description="Filtrar por ID do tipo de ocorrência")
    regiao_id: Optional[int] = Query(None, description="Filtrar por ID da região")
    data_ocorrencia: Optional[date] = Query(None, description="Filtrar por data da ocorrência (AAAA-MM-DD)")
    arquivado: Optional[str] = Query("N", description="Filtrar por arquivado (S/N), padrão N")


class OcorrenciaWithPareceresOut(OcorrenciaOut):
    pareceres: List[ParecerOut] = []

    class Config:
        from_attributes = True
