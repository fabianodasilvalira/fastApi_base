from fastapi import FastAPI

from app.db.session import engine as async_engine
from app.db.base_class import Base
# Importar todos os modelos para que o SQLAlchemy os reconheça para criação de tabelas
from app.models import ocorrencia, user, parecer, sistemas_autorizados 

from app.routers import ocorrencia as ocorrencia_router
from app.routers import users as usuarios_router # Renomeado para usuarios_router para clareza, mas o arquivo ainda é users.py
from app.routers import parecer as parecer_router
from app.routers import sistemas_autorizados as sistemas_autorizados_router

app = FastAPI(
    title="API de Ocorrências e Gestão", 
    version="0.2.0",
    description="API para gestão de ocorrências, usuários, pareceres e sistemas autorizados."
)

@app.on_event("startup")
async def startup_event():
    async with async_engine.begin() as conn:
        # Em um ambiente de desenvolvimento/teste, pode ser útil recriar as tabelas.
        # await conn.run_sync(Base.metadata.drop_all) # Cuidado: apaga todos os dados!
        await conn.run_sync(Base.metadata.create_all)
    print("Tabelas verificadas/criadas no banco de dados. Startup completo.")

# Incluir os routers existentes
app.include_router(ocorrencia_router.router, prefix="/api/v1/ocorrencias", tags=["Ocorrências"])
app.include_router(usuarios_router.router, prefix="/api/v1/usuarios", tags=["Usuarios"]) # Alterado prefix e tag

# Incluir os novos routers
app.include_router(parecer_router.router, prefix="/api/v1/pareceres", tags=["Pareceres"])
app.include_router(sistemas_autorizados_router.router, prefix="/api/v1/sistemas-autorizados", tags=["Sistemas Autorizados"])


