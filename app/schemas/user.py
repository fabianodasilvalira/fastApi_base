from pydantic import BaseModel, EmailStr, constr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    name: str
    cpf: str # Garantir que o CPF tenha 11 dígitos
    phone: Optional[str] = None
    perfil: str = "Usuário"
    email: EmailStr  # Validação de email
    status: int = 10


class UserCreate(UserBase):  # Herda de UserBase para manter os campos básicos
    password: str  # Adicionando o campo password

    class Config:
        orm_mode = True


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserCheckRequest(BaseModel):
    cpf: str
    phone: str
