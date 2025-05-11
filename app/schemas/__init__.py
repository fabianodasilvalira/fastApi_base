from .user import (
    UserBase, UserCreate, UserUpdate, UserInDBBase, UserOut, Token, TokenPayload,
    EmailVerificationRequest, PasswordResetRequest, PasswordResetConfirm,
    UserValidationRequest, UserValidationResponse, UserRole, CPFField
)
from .ocorrencia_schemas import (
    OcorrenciaBase, OcorrenciaCreate, OcorrenciaUpdate, OcorrenciaOut
)
from .parecer_schemas import (
    ParecerBase, ParecerCreate, ParecerUpdate, ParecerOut
)
from .sistemas_autorizados_schemas import (
    SistemaAutorizadoBase, SistemaAutorizadoCreate, SistemaAutorizadoUpdate,
    SistemaAutorizadoResponse as SistemaAutorizadoOut,  # <- Aqui é o ajuste

)
