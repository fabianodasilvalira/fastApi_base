# app/routers/__init__.py
# Este arquivo registra os roteadores da aplicação.

from fastapi import APIRouter

from . import users # Importa o módulo de rotas de usuários
# from . import items # Exemplo se houvesse rotas para itens

api_router = APIRouter()

# Inclui as rotas de usuários no roteador principal
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Incluir outros roteadores aqui, se necessário
# api_router.include_router(items.router, prefix="/items", tags=["items"])

# Comentários em português:
# - `api_router`: Uma instância de `APIRouter` que agrupará todas as rotas da aplicação.
# - `users.router`: O roteador específico para as operações de usuário (login, registro, etc.).
#   Ele é incluído no `api_router` com um prefixo "/users" e uma tag "users" (útil para a documentação do Swagger UI).
# - Comentários indicam como adicionar mais roteadores (por exemplo, para "items") se a API crescer.

