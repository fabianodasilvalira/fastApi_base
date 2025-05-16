from pydantic import BaseModel, validator, constr
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
    url_file: Optional[constr(max_length=2000)] = None
    cadastro: Optional[datetime] = None
    atualizacao: Optional[datetime] = None
    reg_atualizado: Optional[str] = None

    @validator('parecer_data', 'atualizacao', 'cadastro', pre=True)
    def parse_datetime(cls, value):
        if value in (None, '', '0000-00-00 00:00:00'):
            return None
        try:
            if isinstance(value, datetime):
                return value
            if isinstance(value, int):
                # timestamp pode estar em milissegundos
                if value > 1e12:
                    value = value / 1000
                return datetime.fromtimestamp(value)
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            # Caso o valor seja outro tipo, tenta converter para string e parsear
            return datetime.fromisoformat(str(value))
        except Exception:
            # Qualquer erro retorna None para não quebrar o sistema
            return None

class ParecerCreate(ParecerBase):
    pass

class ParecerUpdate(ParecerBase):
    ocorrencia_id: Optional[int] = None

class ParecerOut(ParecerBase):
    id: int

    class Config:
        from_attributes = True  # Equivalente ao antigo orm_mode
