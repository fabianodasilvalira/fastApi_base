# app/services/user_service.py
from typing import Optional, List
from datetime import datetime, timedelta, timezone

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession # Para SQLAlchemy 1.4+
from sqlalchemy.future import select

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password # verify_password pode ser útil
from app.core.email_utils import (
    send_email_verification_email,
    send_password_reset_email,
    generate_secure_token
)
from app.core.config import settings

class UserService:
    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Busca um usuário pelo ID."""
        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Busca um usuário pelo email."""
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_user_by_email_verification_token(self, db: AsyncSession, token: str) -> Optional[User]:
        """Busca um usuário pelo token de verificação de e-mail."""
        result = await db.execute(select(User).filter(User.email_verification_token == token))
        return result.scalars().first()

    async def get_user_by_password_reset_token(self, db: AsyncSession, token: str) -> Optional[User]:
        """Busca um usuário pelo token de redefinição de senha."""
        result = await db.execute(select(User).filter(User.password_reset_token == token))
        return result.scalars().first()

    async def get_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Busca uma lista de usuários com paginação."""
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """Cria um novo usuário, envia e-mail de verificação."""
        hashed_password = get_password_hash(user_in.password)
        email_verification_token = generate_secure_token()
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
        
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role,
            is_email_verified=False, # E-mail não verificado ao criar
            email_verification_token=email_verification_token,
            token_expiry_date=token_expiry
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        # Envia e-mail de verificação
        if db_user.full_name:
            username = db_user.full_name
        else:
            username = db_user.email
        await send_email_verification_email(
            email_to=db_user.email,
            username=username,
            token=email_verification_token
        )
        return db_user

    async def update_user(
        self, db: AsyncSession, db_user: User, user_in: UserUpdate
    ) -> User:
        """Atualiza um usuário existente."""
        update_data = user_in.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            db_user.hashed_password = hashed_password
            del update_data["password"]

        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def delete_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Deleta um usuário pelo ID."""
        db_user = await self.get_user_by_id(db, user_id=user_id)
        if db_user:
            await db.delete(db_user)
            await db.commit()
        return db_user

    async def verify_email(self, db: AsyncSession, token: str) -> Optional[User]:
        """Verifica o e-mail de um usuário usando o token."""
        user = await self.get_user_by_email_verification_token(db, token=token)
        if not user or not user.token_expiry_date or user.token_expiry_date < datetime.now(timezone.utc):
            # Token inválido, não encontrado ou expirado
            return None 
        
        user.is_email_verified = True
        user.email_verification_token = None # Limpa o token após o uso
        user.token_expiry_date = None
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def request_password_reset_for_email(self, db: AsyncSession, email: EmailStr) -> bool:
        """Gera um token de reset de senha e envia por e-mail."""
        user = await self.get_user_by_email(db, email=email)
        if not user:
            return False # Usuário não encontrado, não vazar essa informação (retorna sucesso genérico na rota)
        
        # Opcional: verificar se o e-mail do usuário já foi verificado antes de permitir reset
        # if not user.is_email_verified:
        #     return False # Ou enviar um e-mail pedindo para verificar primeiro
            
        password_reset_token = generate_secure_token()
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        
        user.password_reset_token = password_reset_token
        user.token_expiry_date = token_expiry
        db.add(user)
        await db.commit()
        await db.refresh(user)

        if user.full_name:
            username = user.full_name
        else:
            username = user.email
        await send_password_reset_email(
            email_to=user.email,
            username=username,
            token=password_reset_token
        )
        return True

    async def reset_password(self, db: AsyncSession, token: str, new_password: str) -> Optional[User]:
        """Redefine a senha do usuário usando o token de reset."""
        user = await self.get_user_by_password_reset_token(db, token=token)
        if not user or not user.token_expiry_date or user.token_expiry_date < datetime.now(timezone.utc):
            # Token inválido, não encontrado ou expirado
            return None
        
        user.hashed_password = get_password_hash(new_password)
        user.password_reset_token = None # Limpa o token após o uso
        user.token_expiry_date = None
        # Opcional: Forçar a verificação do e-mail novamente se não estiver verificado
        # if not user.is_email_verified:
        #     user.is_email_verified = True 
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def request_new_email_verification_token(self, db: AsyncSession, email: EmailStr) -> bool:
        """Gera um novo token de verificação de e-mail e envia por e-mail."""
        user = await self.get_user_by_email(db, email=email)
        if not user:
            return False # Usuário não encontrado
        if user.is_email_verified:
            return False # E-mail já verificado

        email_verification_token = generate_secure_token()
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)

        user.email_verification_token = email_verification_token
        user.token_expiry_date = token_expiry
        db.add(user)
        await db.commit()
        await db.refresh(user)

        if user.full_name:
            username = user.full_name
        else:
            username = user.email
        await send_email_verification_email(
            email_to=user.email,
            username=username,
            token=email_verification_token
        )
        return True

# Instância do serviço para ser importada e usada em outros lugares
user_service = UserService()

# Comentários em português:
# - `get_user_by_email_verification_token`, `get_user_by_password_reset_token`: Novos métodos para buscar usuários por tokens específicos.
# - `create_user` modificado:
#   - Define `is_email_verified=False`.
#   - Gera `email_verification_token` e `token_expiry_date`.
#   - Envia e-mail de verificação após salvar o usuário.
# - `verify_email`:
#   - Busca usuário pelo `email_verification_token`.
#   - Verifica se o token é válido e não expirou.
#   - Se válido, define `is_email_verified=True` e limpa o token.
# - `request_password_reset_for_email`:
#   - Busca usuário pelo e-mail.
#   - Gera `password_reset_token` e `token_expiry_date`.
#   - Envia e-mail com o link de redefinição.
# - `reset_password`:
#   - Busca usuário pelo `password_reset_token`.
#   - Verifica se o token é válido e não expirou.
#   - Se válido, atualiza a senha com hash e limpa o token.
# - `request_new_email_verification_token`:
#   - Permite que um usuário não verificado solicite um novo e-mail de verificação.
# - Todas as interações com o banco de dados são assíncronas.
# - Utiliza `generate_secure_token` e funções de envio de e-mail de `email_utils.py`.
# - Utiliza `settings` de `config.py` para durações de expiração de token e URL base.

