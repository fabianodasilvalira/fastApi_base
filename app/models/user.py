from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from enum import Enum
import datetime

from app.db.base_class import Base

class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENTE = "cliente"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), index=True)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.CLIENTE, nullable=False)

    # Novos campos para verificação de e-mail e reset de senha
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), unique=True, index=True, nullable=True)
    password_reset_token = Column(String(255), unique=True, index=True, nullable=True)
    token_expiry_date = Column(DateTime, nullable=True)

    # Adicionar relacionamentos se necessário, por exemplo, com um perfil de usuário
    # profile = relationship("Profile", back_populates="user", uselist=False) # Exemplo

# Comentários em português:
# - O modelo `User` define a estrutura da tabela de usuários no banco de dados.
# - `id`: Chave primária auto-incrementável.
# - `email`: E-mail do usuário, deve ser único.
# - `hashed_password`: Senha do usuário armazenada de forma segura (hash).
# - `full_name`: Nome completo do usuário.
# - `role`: Define o papel do usuário (Admin ou Cliente), usando um Enum para garantir consistência.
#   Por padrão, um novo usuário é um Cliente.
# - `is_email_verified`: Booleano que indica se o e-mail do usuário foi verificado. Padrão é False.
# - `email_verification_token`: Token único usado para verificar o e-mail do usuário. Nulável.
# - `password_reset_token`: Token único usado para o processo de reset de senha. Nulável.
# - `token_expiry_date`: Data e hora em que os tokens (verificação ou reset) expiram. Nulável.
# - A classe `UserRole` é um Enum que define os possíveis papéis de usuário.
# - A importação `from app.db.base_class import Base` é resolvida pois `base_class.py` já existe.

