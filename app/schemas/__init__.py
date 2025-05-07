# app/schemas/__init__.py
# Este arquivo pode ser usado para expor os esquemas Pydantic.

from .user import UserCreate, UserOut, UserUpdate, UserInDBBase, UserRole # Adicionado UserRole
from .token import Token, TokenPayload

