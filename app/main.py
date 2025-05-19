from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.db.session import engine as async_engine
from app.db.base_class import Base
from app.models import ocorrencia, user, parecer, sistemas_autorizados

from app.api.v1.routers import auth as auth_router
from app.api.v1.routers import ocorrencia as ocorrencia_router
from app.api.v1.routers import users as usuarios_router
from app.api.v1.routers import parecer as parecer_router
from app.api.v1.routers import sistemas_autorizados as sistemas_autorizados_router

app = FastAPI(
    title="Ami backend",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    async with async_engine.begin() as conn:
        # Cuidado ao usar drop_all! Descomente com responsabilidade.
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Tabelas verificadas/criadas no banco de dados. Startup completo.")

# Routers
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(ocorrencia_router.router, prefix="/api/v1/ocorrencias", tags=["Ocorrências"])
app.include_router(usuarios_router.router, prefix="/api/v1/usuarios", tags=["Usuários"])
app.include_router(parecer_router.router, prefix="/api/v1/pareceres", tags=["Pareceres"])
app.include_router(sistemas_autorizados_router.router, prefix="/api/v1/sistemas-autorizados", tags=["Sistemas Autorizados"])

# ✅ Swagger com suporte a JWT
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Aplica globalmente a segurança aos endpoints protegidos
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation.setdefault("security", []).append({"BearerAuth": []})

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
