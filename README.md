# BetterEdge Backend

Sistema de gestão de investimentos e portfólio financeiro com API REST desenvolvido em FastAPI.

## 🌐 Acesso em Produção

### 🚀 Ambiente de Produção
- **URL**: https://betteredge-backend-production.up.railway.app/
- **Documentação da API**: https://betteredge-backend-production.up.railway.app/docs

### 👤 Usuário Admin Padrão
- **Email**: `admin@betteredge.com`
- **Senha**: `admin123`

### 🔑 Como Fazer Login
```bash
curl -X POST "https://betteredge-backend-production.up.railway.app/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@betteredge.com", "password": "admin123"}'
```

## 📋 Descrição

O BetterEdge Backend é uma API REST que oferece funcionalidades para:
- **Autenticação de usuários** com JWT
- **Gestão de clientes** 
- **Catálogo de ativos financeiros** (ações, fundos, etc.)
- **Alocações de portfólio** por cliente
- **Transações financeiras** (depósitos, saques)

## 🚀 Setup do Ambiente

### Pré-requisitos
- Python 3.10+
- pip
- PostgreSQL

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd betteredge-backend
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
cp env.example .env

# Edite o arquivo .env com suas configurações
nano .env
```

### 5. Execute as migrações do banco
```bash
alembic upgrade head
```

### 6. Inicie o servidor
```bash
python start.sh
# ou
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

O servidor estará rodando em: http://localhost:8000

## 📚 Documentação da API

### Documentação Interativa (Swagger UI)
Acesse: http://localhost:8000/docs

### Documentação Alternativa (ReDoc)
Acesse: http://localhost:8000/redoc

### Endpoints Principais

#### Autenticação
- `POST /auth/register` - Registrar novo usuário
- `POST /auth/login` - Login do usuário
- `GET /auth/me` - Obter dados do usuário logado

#### Clientes
- `GET /clients/` - Listar clientes
- `POST /clients/` - Criar cliente
- `GET /clients/{id}` - Obter cliente por ID
- `PUT /clients/{id}` - Atualizar cliente
- `DELETE /clients/{id}` - Deletar cliente

#### Ativos
- `GET /assets/` - Listar ativos
- `POST /assets/` - Criar ativo
- `GET /assets/{id}` - Obter ativo por ID
- `PUT /assets/{id}/update-price` - Atualizar preço do ativo
- `GET /assets/search` - Buscar ativos

#### Alocações
- `GET /allocations/` - Listar alocações
- `POST /allocations/` - Criar alocação
- `GET /allocations/{id}` - Obter alocação por ID
- `PUT /allocations/{id}` - Atualizar alocação
- `DELETE /allocations/{id}` - Deletar alocação

#### Transações
- `GET /transactions/` - Listar transações
- `POST /transactions/` - Criar transação
- `GET /transactions/{id}` - Obter transação por ID

## 🧪 Testes

### Estrutura dos Testes

```
tests/
├── api/                    # Testes de integração da API
│   ├── test_auth_api.py
│   ├── test_clients_api.py
│   ├── test_assets_api.py
│   ├── test_allocations_api.py
│   └── test_transactions_api.py
├── services/               # Testes unitários dos serviços
│   ├── test_auth_service.py
│   ├── test_client_service.py
│   ├── test_asset_service.py
│   ├── test_allocation_service.py
│   └── test_transaction_service.py
├── conftest.py            # Configurações do pytest
└── README.md              # Documentação detalhada dos testes
```

### Como Executar os Testes

#### Todos os testes
```bash
source venv/bin/activate
pytest
```

#### Testes de API (integração)
```bash
pytest tests/api/
```

#### Testes de Serviços (unitários)
```bash
pytest tests/services/
```

#### Teste específico
```bash
pytest tests/services/test_auth_service.py
```

#### Teste com verbose
```bash
pytest tests/services/test_auth_service.py -v
```

#### Teste com cobertura
```bash
pytest --cov=app tests/
```

### Tipos de Testes

1. **Testes de API**: Testam os endpoints HTTP com mocks dos serviços
2. **Testes de Serviços**: Testam a lógica de negócio isoladamente com mocks do banco de dados

Para mais detalhes sobre os testes, consulte: [tests/README.md](tests/README.md)

## 🗄️ Banco de Dados

O projeto usa PostgreSQL e Alembic para migrações.

### Comandos do Alembic
```bash
# Aplicar migrações
alembic upgrade head

# Criar nova migração
alembic revision --autogenerate -m "descrição da migração"

# Reverter migração
alembic downgrade -1
```

## 🌱 Seed do Banco de Dados

### Executar seed
```bash
# Com Docker
docker compose exec backend python seed.py

# Local (com venv ativado)
python seed.py
```

* Já é executado no `docker compose up`

### O que o seed cria:
- **👤 Usuário Admin**: `admin@betteredge.com` (senha: `admin123`)
- **👥 8 Clientes**: João Silva, Maria Santos, Pedro Oliveira, etc.
- **📈 48 Ativos**: AAPL, MSFT, GOOGL, AMZN, TSLA, ETFs, Crypto, etc.

### Login como Admin:
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@betteredge.com", "password": "admin123"}'
```

## 🛠️ Desenvolvimento

### Estrutura do Projeto
```
app/
├── api/                   # Endpoints da API
├── core/                  # Configurações centrais
├── models/                # Modelos do banco de dados
├── schemas/               # Schemas Pydantic
├── services/              # Lógica de negócio
└── main.py               # Aplicação principal

alembic/                  # Migrações do banco
tests/                    # Testes
```

### Padrões Utilizados
- **FastAPI** para API REST
- **SQLAlchemy** para ORM
- **Pydantic** para validação de dados
- **Alembic** para migrações
- **JWT** para autenticação
- **Pytest** para testes

## 📝 Variáveis de Ambiente

Principais variáveis no arquivo `.env`:

```env
DATABASE_URL=postgresql+asyncpg://invest:investpw@localhost/investdb
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
YAHOO_FINANCE_BASE_URL=https://query1.finance.yahoo.com/v8/finance/chart
ALLOWED_ORIGINS=["http://localhost:3000", "http://frontend:3000"]
```

## 🚀 Deploy

### Docker Compose (Recomendado)
```bash
# Iniciar todos os serviços (PostgreSQL, Redis, Backend)
docker compose up --build -d

# Ver logs
docker compose logs -f

# Parar serviços
docker compose down
```

### Docker (Apenas Backend)
```bash
# Build da imagem
docker build -t betteredge-backend .

# Executar container
docker run -p 8000:8000 betteredge-backend
```

### Produção
1. Configure as variáveis de ambiente de produção
2. Configure um servidor PostgreSQL
3. Configure um servidor Redis
4. Use um servidor WSGI como Gunicorn

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação da API em `/docs`
2. Consulte os testes para exemplos de uso
3. Verifique os logs do servidor

---

**Desenvolvido com ❤️ usando FastAPI**
