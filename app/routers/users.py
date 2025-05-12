# app/routers/users.py
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app import schemas
from app.core.dependencies import get_db, require_admin_user
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/", response_model=List[UserOut])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1)
) -> List[UserOut]:
    users = await user_service.get_all_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserOut)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)) -> Any:
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    return user


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> Any:
    try:
        return await user_service.create_user(db=db, user_in=user_in)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail ou CPF já cadastrado."
        )

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(get_db)) -> Any:
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return await user_service.update_user(db=db, db_user=user, user_in=user_in)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)) -> None:
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    await user_service.delete_user(db=db, db_user=user)
