from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str = Field(..., description="Token de acesso JWT")
    refresh_token: str = Field(..., description="Token de refresh para renovar o token de acesso")
    token_type: str = Field(..., description="Tipo de token (bearer)")
    user: Dict[str, Any] = Field(..., description="Dados do usuário autenticado")

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    perfil: Optional[str] = None


