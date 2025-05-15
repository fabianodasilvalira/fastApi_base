# Define a imagem base
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de dependências
COPY ./requirements.txt /app/requirements.txt

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Instala dependências do sistema, incluindo netcat
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*


# Copia o restante da aplicação
COPY ./app /app/app
#COPY ./.env /app/.env
#COPY ./alembic.ini /app/alembic.ini
#COPY ./alembic /app/alembic



# Expõe a porta que a aplicação vai rodar
EXPOSE 8000

# Comando para rodar a aplicação
# O entrypoint.sh será criado depois e lidará com as migrações
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

