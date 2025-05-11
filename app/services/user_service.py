# app/services/user_service.py
import logging
import os # Importar os
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

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

TEST_MODE_AUTO_VERIFY_EMAIL = os.getenv("TEST_MODE_AUTO_VERIFY_EMAIL", "false").lower() == "true"
if TEST_MODE_AUTO_VERIFY_EMAIL:
    logger.warning("MODO DE TESTE ATIVO: E-mails de novos usuários serão auto-verificados.")

class UserService:
    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        try:
            result = await db.execute(select(User).filter(User.id == user_id))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Erro de banco de dados ao buscar usuário por ID {user_id}: {e}")
            # Não levantar exceção aqui, deixar o router tratar o None e retornar 404 ou 500
            return None

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        try:
            result = await db.execute(select(User).filter(User.email == email))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Erro de banco de dados ao buscar usuário por e-mail {email}: {e}")
            return None

    async def get_user_by_cpf(self, db: AsyncSession, cpf: str) -> Optional[User]:
        try:
            result = await db.execute(select(User).filter(User.cpf == cpf))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Erro de banco de dados ao buscar usuário por CPF {cpf}: {e}")
            return None

    async def get_user_by_email_verification_token(self, db: AsyncSession, token: str) -> Optional[User]:
        try:
            result = await db.execute(select(User).filter(User.email_verification_token == token))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Erro de banco de dados ao buscar usuário por token de verificação: {e}")
            return None

    async def get_user_by_password_reset_token(self, db: AsyncSession, token: str) -> Optional[User]:
        try:
            result = await db.execute(select(User).filter(User.password_reset_token == token))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Erro de banco de dados ao buscar usuário por token de reset: {e}")
            return None

    async def get_users(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        try:
            result = await db.execute(select(User).offset(skip).limit(limit))
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Erro de banco de dados ao buscar lista de usuários: {e}")
            return [] # Retornar lista vazia em caso de erro, o router pode decidir se isso é um 500

    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        hashed_password = get_password_hash(user_in.password)
        email_verification_token = generate_secure_token()
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)

        db_user = User(
            email=user_in.email,
            cpf=user_in.cpf, # Adicionado CPF
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role,
            is_email_verified=True if TEST_MODE_AUTO_VERIFY_EMAIL else False,
            email_verification_token=None if TEST_MODE_AUTO_VERIFY_EMAIL else email_verification_token,
            token_expiry_date=None if TEST_MODE_AUTO_VERIFY_EMAIL else token_expiry
        )

        try:
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
        except IntegrityError as e: # Erro específico para violação de constraint (e.g. unique)
            await db.rollback()
            logger.error(f"Erro de integridade ao criar usuário (e-mail/CPF duplicado?): {e}")
            raise e # Repassar para o router tratar como 409 Conflict
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro de banco de dados ao criar usuário: {e}")
            raise e # Repassar para o router tratar como 500

        if not TEST_MODE_AUTO_VERIFY_EMAIL:
            try:
                username = db_user.full_name or db_user.email
                await send_email_verification_email(
                    email_to=db_user.email,
                    username=username,
                    token=email_verification_token
                )
            except Exception as e:
                logger.warning(f"Falha ao enviar e-mail de verificação para {db_user.email}: {e}")
                # Não levantar exceção aqui, o usuário foi criado.
        return db_user

    async def update_user(self, db: AsyncSession, db_user: User, user_in: UserUpdate) -> User:
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
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Erro de integridade ao atualizar usuário {db_user.id} (e-mail/CPF duplicado?): {e}")
            raise e
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro de banco de dados ao atualizar usuário {db_user.id}: {e}")
            raise e

    async def delete_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        try:
            db_user = await self.get_user_by_id(db, user_id=user_id)
            if db_user:
                await db.delete(db_user)
                await db.commit()
            return db_user
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro de banco de dados ao deletar usuário {user_id}: {e}")
            # Retornar None ou levantar a exceção para o router decidir
            # Se levantar, o router pode dar um 500 mais específico.
            # Se retornar None, o router pode interpretar como "não encontrado para deleção" ou erro.
            # Por consistência com get_user_by_id, vamos retornar None e deixar o router checar.
            # No entanto, para delete, uma falha no commit é mais crítica.
            raise e # Melhor levantar para o router saber que houve falha no DB.

    async def verify_email(self, db: AsyncSession, token: str) -> Optional[User]:
        try:
            user = await self.get_user_by_email_verification_token(db, token=token)
            if not user or not user.token_expiry_date or user.token_expiry_date < datetime.now(timezone.utc):
                return None # Token inválido ou expirado

            user.is_email_verified = True
            user.email_verification_token = None
            user.token_expiry_date = None

            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro de banco de dados ao verificar e-mail com token {token[:10]}...: {e}")
            raise e

    async def request_password_reset_for_email(self, db: AsyncSession, email: EmailStr) -> bool:
        try:
            user = await self.get_user_by_email(db, email=email)
            if not user:
                logger.info(f"Solicitação de reset de senha para e-mail não cadastrado: {email}")
                return False # Não vazar informação

            password_reset_token = generate_secure_token()
            token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

            user.password_reset_token = password_reset_token
            user.token_expiry_date = token_expiry

            db.add(user)
            await db.commit()

            try:
                username = user.full_name or user.email
                await send_password_reset_email(
                    email_to=user.email,
                    username=username,
                    token=password_reset_token
                )
            except Exception as e:
                logger.warning(f"Falha ao enviar e-mail de reset de senha para {user.email}: {e}")
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro de banco de dados ao solicitar reset de senha para {email}: {e}")
            raise e # Levantar para o router tratar

    async def reset_password(self, db: AsyncSession, token: str, new_password: str) -> Optional[User]:
        try:
            user = await self.get_user_by_password_reset_token(db, token=token)
            if not user or not user.token_expiry_date or user.token_expiry_date < datetime.now(timezone.utc):
                return None # Token inválido ou expirado

            user.hashed_password = get_password_hash(new_password)
            user.password_reset_token = None
            user.token_expiry_date = None

            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro de banco de dados ao redefinir senha com token {token[:10]}...: {e}")
            raise e

    async def request_new_email_verification_token(self, db: AsyncSession, email: EmailStr) -> bool:
        try:
            user = await self.get_user_by_email(db, email=email)
            if not user:
                logger.info(f"Solicitação de novo token de verificação para e-mail não cadastrado: {email}")
                return False
            if user.is_email_verified:
                logger.info(f"Solicitação de novo token de verificação para e-mail já verificado: {email}")
                return False 

            email_verification_token = generate_secure_token()
            token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)

            user.email_verification_token = email_verification_token
            user.token_expiry_date = token_expiry

            db.add(user)
            await db.commit()

            try:
                username = user.full_name or user.email
                await send_email_verification_email(
                    email_to=user.email,
                    username=username,
                    token=email_verification_token
                )
            except Exception as e:
                logger.warning(f"Falha ao reenviar e-mail de verificação para {user.email}: {e}")
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Erro de banco de dados ao solicitar novo token de verificação para {email}: {e}")
            raise e

user_service = UserService()

