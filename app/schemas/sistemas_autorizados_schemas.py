from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SistemaAutorizadoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: Optional[bool] = True

class SistemaAutorizadoCreate(SistemaAutorizadoBase):
    pass

class SistemaAutorizadoUpdate(SistemaAutorizadoBase):
    nome: Optional[str] = None # Todos os campos são opcionais na atualização
    token: Optional[str] = None # Permitir atualização de token se necessário, ou remover se token é imutável pós-criação
    pass

class SistemaAutorizadoResponse(SistemaAutorizadoBase):
    id: int
    data_criacao: datetime
    ultima_atividade: Optional[datetime] = None

    class Config:
        from_attributes = True # Alterado de orm_mode para Pydantic v2

class SistemaAutorizadoComTokenResponse(SistemaAutorizadoResponse):
    token: str

