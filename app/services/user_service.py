from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app import models, schemas
from app.core.security import get_password_hash, verify_password

from app.schemas.user import UserUpdate, UserCreate


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

    @staticmethod
    async def create_user(db: AsyncSession, user_in: UserCreate):
        hashed_password = get_password_hash(user_in.password)
        user = models.User(
            username=user_in.username,
            name=user_in.name,
            cpf=user_in.cpf,
            phone=user_in.phone,
            perfil=user_in.perfil,
            email=user_in.email,
            status=user_in.status,
            password_hash=hashed_password
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
