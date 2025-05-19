from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TipoOcorrenciaBase(BaseModel):
    nome: str
    ativo: str  # 'S' ou 'N'

class TipoOcorrenciaCreate(TipoOcorrenciaBase):
    pass  # mesma estrutura para criação

class TipoOcorrenciaUpdate(BaseModel):
    nome: Optional[str] = None
    ativo: Optional[str] = None

class TipoOcorrenciaInDBBase(TipoOcorrenciaBase):
    id: int
    cadastro: datetime
    atualizacao: Optional[datetime]

    class Config:
        orm_mode = True

class TipoOcorrenciaOut(TipoOcorrenciaInDBBase):
    pass
