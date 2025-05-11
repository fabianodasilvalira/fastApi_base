from typing import Optional, Any, Annotated
from enum import Enum
from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime

# Enum para Role
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

# CPF validator function
def validate_cpf(value: str) -> str:
    if not value:
        return value

    cpf = ''.join(filter(str.isdigit, value))

    if len(cpf) != 11:
        raise ValueError("CPF deve conter 11 dígitos numéricos.")

    if cpf == cpf[0] * 11:
        raise ValueError("CPF inválido: todos os dígitos são iguais.")

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dv1 = 0 if soma % 11 < 2 else 11 - (soma % 11)
    if dv1 != int(cpf[9]):
        raise ValueError("CPF inválido: primeiro dígito verificador não confere.")

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dv2 = 0 if soma % 11 < 2 else 11 - (soma % 11)
    if dv2 != int(cpf[10]):
        raise ValueError("CPF inválido: segundo dígito verificador não confere.")

    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


# Define CPFField usando Annotated + Field (opcional)
CPFField = Annotated[str, Field(..., min_length=11, max_length=14)]


# Base
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    cpf: Optional[CPFField] = None
    is_active: Optional[bool] = True
    is_email_verified: Optional[bool] = False
    role: Optional[UserRole] = UserRole.USER

    @validator('cpf')
    def cpf_validator(cls, v):
        return validate_cpf(v)


# Criação de usuário
class UserCreate(UserBase):
    email: EmailStr
    password: str
    full_name: str
    cpf: CPFField


# Atualização de usuário
class UserUpdate(UserBase):
    password: Optional[str] = None


# Modelo interno (usado no banco)
class UserInDBBase(UserBase):
    id: int
    hashed_password: str

    class Config:
        orm_mode = True


# Saída da API
class UserOut(UserBase):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    cpf: Optional[CPFField] = None
    is_active: bool
    is_email_verified: bool
    role: UserRole
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Schemas de autenticação
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None
    exp: Optional[datetime] = None


# Verificação de e-mail e senha
class EmailVerificationRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    new_password: str = Field(..., min_length=8)


# Validação de cadastro
class UserValidationRequest(BaseModel):
    email: Optional[EmailStr] = None
    cpf: Optional[CPFField] = None

    @validator('cpf', pre=True, always=True)
    def check_at_least_one_field(cls, v, values, **kwargs):
        if not v and not values.get('email'):
            raise ValueError("Deve ser fornecido ao menos um campo: email ou CPF.")
        return v


class UserValidationResponse(BaseModel):
    is_registered: bool
    message: str
    user_details: Optional[UserOut] = None
