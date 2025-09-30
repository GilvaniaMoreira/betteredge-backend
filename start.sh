#!/bin/bash

# Aguardar simples pelo banco de dados
echo "Aguardando o banco de dados ficar pronto..."
sleep 10

# Executar migrações
echo "Executando migrações do banco de dados..."
alembic upgrade head

# Iniciar a aplicação
echo "Iniciando aplicação..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
