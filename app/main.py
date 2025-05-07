# app/main.py
from fastapi import FastAPI
from dotenv import load_dotenv
import os

from app.routers import api_router # Roteador principal com todas as rotas da API
from app.db.session import engine, AsyncSessionLocal # Engine e SessionLocal para o DB
from app.db.base_class import Base # Base para criar tabelas (se necessário no main)

# Carrega variáveis de ambiente do .env que está na raiz do projeto /app no Docker
# Isso é importante para que o Uvicorn iniciado pelo Dockerfile tenha acesso às variáveis
# Se o .env estiver em outro lugar em relação ao main.py, ajuste o path.
# No docker-compose, o .env da raiz do projeto local é montado em /app/.env no container.
load_dotenv(dotenv_path="/app/.env")

app = FastAPI(
    title="API Completa com FastAPI, MySQL e Docker",
    description="Uma API com autenticação JWT, perfis de usuário, e migrações automáticas.",
    version="0.1.0",
    # openapi_url="/api/v1/openapi.json" # Exemplo de customização da URL do OpenAPI spec
)

# Evento de startup da aplicação
@app.on_event("startup")
async def startup_event():
    """
    Este evento é executado quando a aplicação FastAPI inicia.
    Pode ser usado para inicializar conexões com banco de dados, carregar modelos de ML, etc.
    A criação das tabelas via `Base.metadata.create_all(bind=engine)` é geralmente
    tratada pelo Alembic (migrações), então não é estritamente necessária aqui se Alembic
    estiver configurado para rodar no startup (como no docker-compose.yml).
    No entanto, se você não estiver usando Alembic para criar tabelas iniciais ou para
    um ambiente de desenvolvimento simples, você pode descomentar a linha abaixo.
    Lembre-se que `create_all` não realiza migrações (alterações em tabelas existentes).
    """
    # async with engine.begin() as conn:
    #     # await conn.run_sync(Base.metadata.drop_all) # Cuidado: apaga todas as tabelas
    #     await conn.run_sync(Base.metadata.create_all)
    print("Aplicação FastAPI iniciada.")
    # Aqui você pode adicionar lógicas como: verificar conexão com DB, etc.

# Evento de shutdown da aplicação
@app.on_event("shutdown")
async def shutdown_event():
    """
    Este evento é executado quando a aplicação FastAPI está prestes a parar.
    Pode ser usado para fechar conexões com banco de dados, limpar recursos, etc.
    """
    # await engine.dispose() # Fecha as conexões do pool da engine assíncrona
    print("Aplicação FastAPI encerrada.")

# Inclui o roteador principal da API
# Todas as rotas definidas em app.routers (ex: /users, /login) estarão disponíveis
app.include_router(api_router, prefix="") # Pode adicionar um prefixo global aqui se desejar, ex: "/api/v1"

# Rota de health check básica
@app.get("/health", tags=["healthcheck"])
async def health_check():
    """Verifica a saúde da aplicação."""
    return {"status": "ok"}

# Comentários em português:
# - `app`: Instância principal da aplicação FastAPI.
# - `load_dotenv(dotenv_path="/app/.env")`: Garante que as variáveis de ambiente sejam carregadas
#   a partir do arquivo .env localizado em /app/.env dentro do container Docker.
#   O `docker-compose.yml` monta o .env do host para este local.
# - `startup_event`: Função executada no início da aplicação. Ideal para inicializações.
#   A criação de tabelas com `Base.metadata.create_all` é comentada porque o Alembic
#   já está configurado para rodar as migrações no `docker-compose.yml`.
# - `shutdown_event`: Função executada ao finalizar a aplicação. Ideal para limpeza de recursos.
# - `app.include_router(api_router)`: Adiciona todas as rotas definidas em `app.routers` à aplicação.
# - `/health`: Uma rota simples de health check para verificar se a API está rodando.

