# API FastAPI Completa com MySQL e Docker

Este projeto contém o código-fonte completo de uma API desenvolvida com FastAPI, utilizando MySQL como banco de dados e Docker para containerização. A API inclui autenticação JWT, gerenciamento de usuários com perfis (Admin e Cliente) e migrações automáticas de banco de dados com Alembic.

## Estrutura do Projeto

```
fastapi_project/
├── app/
│   ├── core/         # Lógica central (autenticação, dependências)
│   ├── db/           # Configuração do banco de dados, modelos base, sessões e migrações Alembic
│   ├── models/       # Modelos SQLAlchemy (ex: User)
│   ├── routers/      # Módulos de rotas da API (ex: users.py)
│   ├── schemas/      # Esquemas Pydantic para validação de dados e serialização
│   ├── services/     # Lógica de negócio (ex: user_service.py)
│   └── main.py       # Ponto de entrada da aplicação FastAPI
├── .env              # Arquivo de variáveis de ambiente (configurações de DB, JWT, etc.)
├── Dockerfile        # Define a imagem Docker para a aplicação FastAPI
├── docker-compose.yml # Orquestra os containers da aplicação e do banco de dados MySQL
├── requirements.txt  # Lista de dependências Python
└── README.md         # Este arquivo
```

## Pré-requisitos

- Docker
- Docker Compose

## Como Executar

1.  **Clone o projeto** (ou extraia o arquivo ZIP em um diretório de sua escolha).
2.  **Configure as variáveis de ambiente:**
    *   Renomeie ou copie o arquivo `.env.example` (se fornecido) para `.env` na raiz do projeto (`fastapi_project`).
    *   Ajuste as variáveis no arquivo `.env` conforme necessário, especialmente:
        *   `DATABASE_URL`: Verifique se o usuário, senha e nome do banco correspondem ao que será usado pelo MySQL no Docker.
        *   `SECRET_KEY`: Uma chave secreta forte para a codificação JWT.
        *   `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_ROOT_PASSWORD`: Usadas pelo container do MySQL no `docker-compose.yml`.

    O arquivo `.env` fornecido já contém valores padrão que devem funcionar para um ambiente de desenvolvimento local com Docker:
    ```env
    DATABASE_URL=mysql+aiomysql://user:password@db:3306/fastapi_db
    SECRET_KEY=your_secret_key_please_change_me
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    REFRESH_TOKEN_EXPIRE_DAYS=7

    # Variáveis para o container do MySQL (usadas no docker-compose.yml)
    MYSQL_DATABASE=fastapi_db
    MYSQL_USER=user
    MYSQL_PASSWORD=password
    MYSQL_ROOT_PASSWORD=root_password_change_me
    ```
    **Importante:** Altere `SECRET_KEY`, `MYSQL_PASSWORD` e `MYSQL_ROOT_PASSWORD` para valores seguros em um ambiente de produção.

3.  **Construa e inicie os containers Docker:**
    Navegue até o diretório raiz do projeto (`fastapi_project`) pelo terminal e execute:
    ```bash
    docker-compose up --build
    ```
    Este comando irá construir a imagem da aplicação FastAPI e iniciar os containers da aplicação e do banco de dados MySQL. As migrações do Alembic (definidas em `app/db/migrations`) serão aplicadas automaticamente quando o container da aplicação iniciar, conforme configurado no `docker-compose.yml`.

4.  **Acesse a API:**
    *   A API estará disponível em: `http://localhost:8000`
    *   A documentação interativa (Swagger UI) estará disponível em: `http://localhost:8000/docs`
    *   A especificação OpenAPI estará em: `http://localhost:8000/openapi.json`

## Testes e Validação

Recomenda-se que você execute os seguintes testes manuais utilizando a interface do Swagger UI (`/docs`) ou uma ferramenta como Postman/Insomnia:

1.  **Criação de Usuários:**
    *   Tente registrar um novo usuário Cliente (`POST /users/register`).
    *   Tente registrar um usuário Admin (você pode modificar o payload no Swagger ou criar um endpoint específico se necessário, ou atualizar um usuário existente para Admin via banco de dados para testes iniciais).

2.  **Login e Geração de Tokens JWT:**
    *   Faça login com um usuário criado (`POST /users/login` com `username` e `password` no corpo do formulário).
    *   Verifique se os tokens de acesso e refresh são retornados.

3.  **Acesso a Rotas Protegidas:**
    *   Tente acessar a rota `GET /users/me` usando o token de acesso obtido (autorize no Swagger UI clicando no botão "Authorize" e colando o `access_token`).
    *   Tente acessar a mesma rota sem o token ou com um token inválido para verificar a proteção.

4.  **Permissões de Admin e Cliente:**
    *   Logado como Admin, tente acessar rotas exclusivas de Admin (ex: `GET /users/`, `GET /users/{user_id}`).
    *   Logado como Cliente, tente acessar as mesmas rotas de Admin e verifique se o acesso é negado (HTTP 403 Forbidden).
    *   Logado como Cliente, verifique se consegue acessar `GET /users/me`.

5.  **Migrações Automáticas:**
    *   Ao iniciar o `docker-compose up`, verifique os logs do container da aplicação para confirmar que as migrações do Alembic (`alembic upgrade head`) foram executadas com sucesso.
    *   Você pode criar uma nova migração (após modificar os modelos em `app/models/`) e reiniciar os containers para ver se ela é aplicada.
        *   Para gerar uma nova revisão de migração (execute dentro do container da app ou localmente com o ambiente Python configurado e `PYTHONPATH` apontando para a raiz do projeto):
            ```bash
            # Dentro do diretório fastapi_project/app/db
            alembic revision -m "nome_da_sua_migracao"
            ```
        *   Edite o arquivo de migração gerado em `app/db/migrations/versions/`.
        *   Reinicie os containers: `docker-compose down && docker-compose up --build`.

## Observações

*   O banco de dados MySQL utiliza um volume Docker (`mysql_data`) para persistir os dados entre reinicializações dos containers. Se você quiser começar com um banco de dados limpo, pode remover este volume com `docker volume rm fastapi_project_mysql_data` (o nome do volume pode variar, verifique com `docker volume ls`).
*   O código está comentado em português para facilitar o entendimento.
*   Este projeto utiliza `aiomysql` como driver assíncrono para o MySQL. Certifique-se de que a `DATABASE_URL` no `.env` está formatada corretamente (`mysql+aiomysql://...`).

Divirta-se explorando a API!

