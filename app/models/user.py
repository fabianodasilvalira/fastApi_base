from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    cpf = Column(String(14), nullable=False, unique=True)
    phone = Column(String(20), nullable=True)
    perfil = Column(String(255), nullable=False, default="Usuário")  # Mudei para String
    auth_key = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    password_reset_token = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, unique=True)
    status = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verification_token = Column(String(255), nullable=True)
