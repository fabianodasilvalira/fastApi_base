from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from starlette import status

from app import models, schemas
from app.core.security import get_password_hash, verify_password

from app.schemas.user import UserUpdate, UserCreate
from app.utils.validadores import validar_cpf, validar_email


class UserService:
    @staticmethod
    async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 10):
        async with db.begin():
            result = await db.execute(
                select(models.User).offset(skip).limit(limit)
            )
            users = result.scalars().all()
        return users

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        async with db.begin():
            result = await db.execute(select(models.User).filter(models.User.id == user_id))
            user = result.scalars().first()
        return user

    from sqlalchemy import select, func
    from fastapi import HTTPException, status

    @staticmethod
    async def create_user(db: AsyncSession, user_in: UserCreate):
        # Garantir que o CPF e E-mail não tenham espaços extras
        cpf = user_in.cpf.strip()
        email = user_in.email.strip().lower()
        username = user_in.username.strip()

        print(f"Verificando CPF: {cpf}, E-mail: {email}, Username: {username}")

        # Verifica se o CPF já está cadastrado
        result = await db.execute(select(models.User).filter(models.User.cpf == cpf))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="CPF já cadastrado."
            )

        # Verifica se o e-mail já está cadastrado (case-insensitive)
        result = await db.execute(select(models.User).filter(func.lower(models.User.email) == email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado."
            )

        # Verifica se o username já está cadastrado
        result = await db.execute(select(models.User).filter(models.User.username == username))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username já cadastrado."
            )

        # Criar o novo usuário
        hashed_password = get_password_hash(user_in.password)
        user = models.User(
            username=username,
            name=user_in.name,
            cpf=cpf,
            phone=user_in.phone,
            perfil=user_in.perfil,
            email=email,
            status=user_in.status,
            password_hash=hashed_password,
            auth_key="auth_key",  # Substitua por geração real se necessário
            verification_token="teste"  # Substitua por geração real se necessário
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_user(db: AsyncSession, db_user: models.User, user_in: UserUpdate):
        if user_in.password:
            db_user.password_hash = get_password_hash(user_in.password)
        db_user.username = user_in.username
        db_user.name = user_in.name
        db_user.cpf = user_in.cpf
        db_user.phone = user_in.phone
        db_user.perfil = user_in.perfil
        db_user.email = user_in.email
        db_user.status = user_in.status
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def delete_user(db: AsyncSession, db_user: models.User):
        await db.delete(db_user)
        await db.commit()


user_service = UserService()
