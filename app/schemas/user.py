from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing_extensions import Dict, Any


class UserBase(BaseModel):
    username: str = Field(..., description="Nome de usuário único para identificação no sistema")
    name: str = Field(..., description="Nome completo do usuário")
    cpf: str = Field(..., description="CPF do usuário no formato XXX.XXX.XXX-XX")
    phone: Optional[str] = Field(None, description="Número de telefone do usuário")
    perfil: str = Field("Usuário", description="Perfil de acesso do usuário no sistema")
    email: EmailStr = Field(..., description="Endereço de e-mail do usuário")
    status: int = Field(10, description="Status do usuário (10=ativo, 0=inativo)")

class UserCreate(UserBase):
    password: str = Field(..., description="Senha para acesso ao sistema")

    class Config:
        orm_mode = True

class UserUpdate(UserBase):
    password: Optional[str] = Field(None, description="Nova senha (deixe em branco para manter a atual)")

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    email: str
    perfil: str
    status: int

    class Config:
        orm_mode = True

class UserCheckRequest(BaseModel):
    cpf: str = Field(..., description="CPF do usuário para verificação")
    phone: str = Field(..., description="Telefone do usuário para verificação")

class LoginInput(BaseModel):
    email: EmailStr = Field(..., description="E-mail do usuário")
    password: str = Field(..., description="Senha do usuário")

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"]  # restringe o valor, melhora docs
    user: Dict[str, Any]

class GovBrAuthRequest(BaseModel):
    redirect_uri: str = Field(..., description="URI de redirecionamento após autenticação no gov.br")


class LogoutResponse(BaseModel):
    message: str