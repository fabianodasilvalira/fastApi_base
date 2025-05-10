from .token import Token, TokenPayload
# Ajustar as importações de user.py para refletir as classes realmente definidas
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDBBase, # Este é o mais próximo de UserInDB, mas pode precisar de alias ou ser usado diretamente
    UserOut,
    UserRole,
    EmailVerificationRequest,
    PasswordResetRequest,
    PasswordResetConfirm
)
# Remover OcorrenciaUpdate da importação se não existir em ocorrencia_schemas.py
from .ocorrencia_schemas import OcorrenciaBase, OcorrenciaCreate, OcorrenciaOut 
from .parecer_schemas import ParecerBase, ParecerCreate, ParecerUpdate, ParecerOut
from .sistemas_autorizados_schemas import (
    SistemaAutorizadoBase,
    SistemaAutorizadoCreate,
    SistemaAutorizadoUpdate,
    SistemaAutorizadoResponse,
    SistemaAutorizadoComTokenResponse
)

__all__ = [
    "Token", 
    "TokenPayload", 
    # Schemas de Usuário
    "UserBase",
    "UserCreate", 
    "UserUpdate", 
    "UserInDBBase", # Usar este no lugar de UserInDB se for o caso
    "UserOut",
    "UserRole",
    "EmailVerificationRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # Schemas de Ocorrência
    "OcorrenciaBase", 
    "OcorrenciaCreate", 
    "OcorrenciaOut",
    # "OcorrenciaUpdate", # Removido se não existir
    # Schemas de Parecer
    "ParecerBase",
    "ParecerCreate",
    "ParecerUpdate",
    "ParecerOut",
    # Schemas de Sistemas Autorizados
    "SistemaAutorizadoBase",
    "SistemaAutorizadoCreate",
    "SistemaAutorizadoUpdate",
    "SistemaAutorizadoResponse",
    "SistemaAutorizadoComTokenResponse"
]

