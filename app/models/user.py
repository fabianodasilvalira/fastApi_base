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

