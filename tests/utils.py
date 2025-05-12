from app.models import User
from app.core.security import create_access_token
from sqlalchemy.ext.asyncio import AsyncSession

async def create_test_user(db: AsyncSession, is_admin=False):
    user = User(email="admin@example.com", hashed_password="hashed", is_admin=is_admin)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

def create_test_token(user: User) -> str:
    return create_access_token(subject=str(user.id))

# Banco de dados fake para testes (você precisa configurar)
async def get_test_db() -> AsyncSession:
    from app.db.session import async_session_maker_test  # deve criar uma session maker só para testes
    async with async_session_maker_test() as session:
        yield session
