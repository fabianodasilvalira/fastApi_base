# app/services/user_service.py
import logging
import os # Importar os
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from app.core.email_utils import (
    send_email_verification_email,
    send_password_reset_email,
    generate_secure_token
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# Verificar se estamos em modo de teste para auto-verificar e-mails
TEST_MODE_AUTO_VERIFY_EMAIL = os.getenv("TEST_MODE_AUTO_VERIFY_EMAIL", "false").lower() == "true"
if TEST_MODE_AUTO_VERIFY_EMAIL:
    logger.warning("MODO DE TESTE ATIVO: E-mails de novos usuários serão auto-verificados.")

class UserService:
    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        try:
            result = await db.execute(select(User).filter(User.id == user_id))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar usuário por ID: {e}")
            return None

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        try:
            result = await db.execute(select(User).filter(User.email == email))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar usuário por e-mail: {e}")
            return None

    async def get_user_by_email_verification_token(self, db: AsyncSession, token: str) -> Optional[User]:
        try:
            result = await db.execute(select(User).filter(User.email_verification_token == token))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar usuário por token de verificação: {e}")
            return None

    async def get_user_by_password_reset_token(self, db: AsyncSession, token: str) -> Optional[User]:
        try:
            result = await db.execute(select(User).filter(User.password_reset_token == token))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar usuário por token de reset: {e}")
            return None

    async def get_users(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        try:
            result = await db.execute(select(User).offset(skip).limit(limit))
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar lista de usuários: {e}")
            return []

    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> Optional[User]:
        hashed_password = get_password_hash(user_in.password)
        email_verification_token = generate_secure_token()
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)

        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role,
            is_email_verified=True if TEST_MODE_AUTO_VERIFY_EMAIL else False, # Modificado aqui
            email_verification_token=None if TEST_MODE_AUTO_VERIFY_EMAIL else email_verification_token, # Modificado aqui
            token_expiry_date=None if TEST_MODE_AUTO_VERIFY_EMAIL else token_expiry # Modificado aqui
        )

        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro ao criar usuário: {e}")
            return None

        # Não enviar e-mail de verificação se auto-verificado em modo de teste
        if not TEST_MODE_AUTO_VERIFY_EMAIL:
            try:
                username = db_user.full_name or db_user.email
                await send_email_verification_email(
                    email_to=db_user.email,
                    username=username,
                    token=email_verification_token # Este token só é relevante se não for auto-verificado
                )
            except Exception as e:
                logger.warning(f"Erro ao enviar e-mail de verificação: {e}")

        return db_user

    async def update_user(self, db: AsyncSession, db_user: User, user_in: UserUpdate) -> Optional[User]:
        update_data = user_in.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            db_user.hashed_password = hashed_password
            del update_data["password"]

        for field, value in update_data.items():
            setattr(db_user, field, value)

        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro ao atualizar usuário: {e}")
            return None

    async def delete_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        try:
            db_user = await self.get_user_by_id(db, user_id=user_id)
            if db_user:
                await db.delete(db_user)
                await db.commit()
            return db_user # Retorna o usuário deletado para confirmação
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro ao deletar usuário: {e}")
            return None

    async def verify_email(self, db: AsyncSession, token: str) -> Optional[User]:
        try:
            user = await self.get_user_by_email_verification_token(db, token=token)
            if not user or not user.token_expiry_date or user.token_expiry_date < datetime.now(timezone.utc):
                return None

            user.is_email_verified = True
            user.email_verification_token = None
            user.token_expiry_date = None

            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro ao verificar e-mail: {e}")
            return None

    async def request_password_reset_for_email(self, db: AsyncSession, email: EmailStr) -> bool:
        try:
            user = await self.get_user_by_email(db, email=email)
            if not user:
                return False # Não vazar informação se o e-mail existe

            password_reset_token = generate_secure_token()
            token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

            user.password_reset_token = password_reset_token
            user.token_expiry_date = token_expiry

            db.add(user)
            await db.commit()
            # Não precisa de refresh aqui, pois não estamos retornando o objeto user imediatamente

            try:
                username = user.full_name or user.email
                await send_password_reset_email(
                    email_to=user.email,
                    username=username,
                    token=password_reset_token
                )
            except Exception as e:
                logger.warning(f"Erro ao enviar e-mail de reset de senha: {e}")
                # Considerar se a falha no envio de e-mail deve reverter a transação do token.
                # Por ora, o token é salvo mesmo que o e-mail falhe.

            return True
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro ao gerar token de reset de senha: {e}")
            return False

    async def reset_password(self, db: AsyncSession, token: str, new_password: str) -> Optional[User]:
        try:
            user = await self.get_user_by_password_reset_token(db, token=token)
            if not user or not user.token_expiry_date or user.token_expiry_date < datetime.now(timezone.utc):
                return None

            user.hashed_password = get_password_hash(new_password)
            user.password_reset_token = None
            user.token_expiry_date = None

            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro ao redefinir senha: {e}")
            return None

    async def request_new_email_verification_token(self, db: AsyncSession, email: EmailStr) -> bool:
        try:
            user = await self.get_user_by_email(db, email=email)
            if not user or user.is_email_verified:
                # Não enviar se usuário não existe ou já está verificado
                return False 

            email_verification_token = generate_secure_token()
            token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)

            user.email_verification_token = email_verification_token
            user.token_expiry_date = token_expiry

            db.add(user)
            await db.commit()
            # Não precisa de refresh aqui

            try:
                username = user.full_name or user.email
                await send_email_verification_email(
                    email_to=user.email,
                    username=username,
                    token=email_verification_token
                )
            except Exception as e:
                logger.warning(f"Erro ao reenviar e-mail de verificação: {e}")

            return True
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro ao gerar novo token de verificação: {e}")
            return False

user_service = UserService()

