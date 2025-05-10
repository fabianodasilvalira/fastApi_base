from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ParecerBase(BaseModel):
    ocorrencia_id: int
    situacao_ocorrencia_id: Optional[int] = None
    parecer_publico: Optional[str] = None
    parecer_privado: Optional[str] = None
    parecer_data: Optional[datetime] = None
    parecer_usuario_id: Optional[int] = None
    encam_orgao_id: Optional[int] = None
    encam_usuario_id: Optional[int] = None
    url_file: Optional[str] = None
    cadastro: Optional[datetime] = None
    atualizacao: Optional[datetime] = None
    reg_atualizado: Optional[str] = None

class ParecerCreate(ParecerBase):
    pass

class ParecerUpdate(ParecerBase):
    # Todos os campos são opcionais na atualização
    ocorrencia_id: Optional[int] = None
    pass # Herda todos os campos de ParecerBase como opcionais implicitamente se não redefinidos

class ParecerOut(ParecerBase):
    id: int

    class Config:
        from_attributes = True # Alterado de orm_mode para Pydantic v2

