from fastapi import FastAPI

from app.db import Base, engine
from app.models import ocorrencia  # importa para garantir criação de tabelas
from app.routers import ocorrencia as ocorrencia_router


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(ocorrencia_router.router)
