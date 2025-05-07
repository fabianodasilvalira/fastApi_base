# app/schemas/user.py
from typing import Optional
from enum import Enum

from pydantic import BaseModel, EmailStr, Field

# Reutiliza o Enum de UserRole definido nos modelos para consistência
# from app.models.user import UserRole # Idealmente, importar se possível

class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENTE = "cliente"

# Propriedades básicas do usuário, compartilhadas por outros esquemas
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="usuario@example.com")
    full_name: Optional[str] = Field(None, example="Nome Completo do Usuário")

# Propriedades para criar um novo usuário
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="senhaSuperF0rte")
    role: UserRole = Field(UserRole.CLIENTE, example="cliente") # Default para cliente

# Propriedades para atualizar um usuário (Admin pode atualizar mais campos)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example="novo_email@example.com")
    full_name: Optional[str] = Field(None, example="Novo Nome Completo")
    password: Optional[str] = Field(None, min_length=8, example="novaSenhaSuperF0rte")
    role: Optional[UserRole] = Field(None, example="admin")
    is_email_verified: Optional[bool] = None # Admin pode verificar email manualmente

# Propriedades armazenadas no DB, mas não necessariamente retornadas sempre
class UserInDBBase(UserBase):
    id: int
    role: UserRole
    is_email_verified: bool # Adicionado aqui para refletir o modelo

    class Config:
        from_atributes = True # Permite que o Pydantic leia dados de objetos ORM

# Propriedades adicionais para retornar ao cliente (sem o hashed_password)
class UserOut(UserInDBBase):
    # is_email_verified já está em UserInDBBase, então será incluído
    pass 

# Schema para solicitar verificação de e-mail ou reenvio de token
class EmailVerificationRequest(BaseModel):
    email: EmailStr = Field(..., example="usuario@example.com")

# Schema para solicitar reset de senha
class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., example="usuario@example.com")

# Schema para confirmar o reset de senha com o token
class PasswordResetConfirm(BaseModel):
    # token: str = Field(..., example="seu_token_de_reset_aqui") # O token virá pela URL
    new_password: str = Field(..., min_length=8, example="novaSenhaSuperF0rte")

# Comentários em português:
# - `UserRole`: Enum para os papéis de usuário.
# - `UserBase`: Campos comuns.
# - `UserCreate`: Para criar usuários. Senha é requerida.
# - `UserUpdate`: Para atualizar usuários. `is_email_verified` adicionado para que Admin possa alterar.
# - `UserInDBBase`: Representa o usuário no DB, agora incluindo `is_email_verified`.
#   `Config.from_atributes = True` (ou `from_attributes = True` em Pydantic V2) é crucial.
# - `UserOut`: Esquema de saída para o cliente. `is_email_verified` será incluído pois está em `UserInDBBase`.
# - `EmailVerificationRequest`: Schema para quando um usuário solicita (ou reenviar) o e-mail de verificação.
# - `PasswordResetRequest`: Schema para quando um usuário solicita o e-mail de recuperação de senha.
# - `PasswordResetConfirm`: Schema para o usuário fornecer a nova senha. O token será parte da URL da rota, não do corpo.

