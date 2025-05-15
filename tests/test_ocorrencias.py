import sys
import os
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.main import app  # Certifique-se de que esse é o entrypoint da sua FastAPI
from app.models import User
from tests.utils import get_test_db, create_test_user, create_test_token

# Adicionar o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Substituir a dependência de banco de dados real pelo banco de dados de testes
app.dependency_overrides[get_async_db] = get_test_db

@pytest.mark.asyncio
async def test_create_ocorrencia():
    # Criar um usuário admin de teste e gerar token
    async for db in get_test_db():  # Consumir o gerador assíncrono corretamente
        user: User = await create_test_user(db, is_admin=True)  # Função para criar usuário de teste
        token = create_test_token(user)  # Função para criar token de autenticação

        headers = {
            "Authorization": f"Bearer {token}",
            "X-API-KEY": "test-api-key"  # Substitua por uma chave de API real ou de teste
        }

        payload = {
            "descricao": "Teste de ocorrência",
            "user_id": user.id  # O ID do usuário criado será usado aqui
        }

        # Usando o AsyncClient de forma assíncrona com base_url
        async with AsyncClient(base_url="http://testserver") as ac:
            response = await ac.post("/ocorrencias/", json=payload, headers=headers)

            assert response.status_code == status.HTTP_201_CREATED
            assert response.json()["descricao"] == "Teste de ocorrência"
