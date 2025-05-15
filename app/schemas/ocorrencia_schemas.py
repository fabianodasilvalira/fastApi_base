# app/schemas/ocorrencia_schemas.py
from typing import Optional, List
from datetime import date, time, datetime

from fastapi import Query
from pydantic import BaseModel, Field

# Importar ParecerOut para o schema OcorrenciaWithPareceresOut
from .parecer_schemas import ParecerOut # Adicionado

class OcorrenciaBase(BaseModel):
    data_ocorrencia: Optional[date] = None
    hora_ocorrencia: Optional[time] = None
    situacao_ocorrencia_id: Optional[int] = None
    tipo_atendimento_id: Optional[int] = None
    programa_id: Optional[int] = None
    tipo_ocorrencia_id: Optional[int] = None
    protocolo: Optional[str] = None
    regiao_id: Optional[int] = None
    sigilo: Optional[str] = Field(None, max_length=1)
    nome_completo: Optional[str] = Field(None, max_length=150)
    endereco: Optional[str] = Field(None, max_length=255)
    fone1: Optional[str] = Field(None, max_length=15)
    fone2: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    url_file: Optional[str] = Field(None, max_length=255)
    assunto: Optional[str] = Field(None, max_length=255)
    mensagem: Optional[str] = None # Text
    encaminhamento_orgao_id: Optional[int] = None
    encaminhamento_usuario_id: Optional[int] = None
    encaminhamento_data: Optional[datetime] = None
    parecer_usuario_id: Optional[int] = None
    parecer_descricao: Optional[str] = None # Text
    parecer_data: Optional[datetime] = None
    notificar: Optional[str] = Field(None, max_length=1)
    notificado: Optional[str] = Field(None, max_length=1)
    situacao_anterior: Optional[int] = None
    programa_anterior: Optional[int] = None
    tipo_atend_anterior: Optional[int] = None
    pessoa_id: Optional[int] = None
    user_id: Optional[int] = None # FK para User
    cadastro: Optional[datetime] = None
    atualizacao: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    arquivado: Optional[str] = Field(None, max_length=1) # S ou N

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

# Novo Schema para filtros opcionais nas listagens de ocorrências
class OcorrenciaFilterParams(BaseModel):
    situacao_ocorrencia_id: Optional[int] = Query(None, description="Filtrar por ID da situação da ocorrência")
    tipo_atendimento_id: Optional[int] = Query(None, description="Filtrar por ID do tipo de atendimento")
    programa_id: Optional[int] = Query(None, description="Filtrar por ID do programa")
    tipo_ocorrencia_id: Optional[int] = Query(None, description="Filtrar por ID do tipo de ocorrência")
    regiao_id: Optional[int] = Query(None, description="Filtrar por ID da região")
    data_ocorrencia: Optional[date] = Query(None, description="Filtrar por data da ocorrência (AAAA-MM-DD)")
    arquivado: Optional[str] = Query("N", description="Filtrar por arquivado (S/N), padrão N se não especificado para rotas que não o tem como padrão") # Padrão N aqui é genérico, será sobreposto na rota se necessário

# Novo Schema para resposta da ocorrência com seus pareceres
class OcorrenciaWithPareceresOut(OcorrenciaOut):
    pareceres: List[ParecerOut] = []

    class Config:
        from_attributes = True

