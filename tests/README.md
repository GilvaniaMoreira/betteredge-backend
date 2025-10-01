# Guia de Testes - BetterEdge Backend

## 📋 Estratégia de Testes

Este projeto utiliza duas abordagens de teste complementares:

### 1. **Testes de API** (`tests/api/`)
- **Objetivo**: Testar endpoints HTTP completos
- **Mocking**: Serviços são mockados para isolar a API
- **Velocidade**: Rápida
- **Cobertura**: Fluxos completos de requisição/resposta

```python
# Exemplo: test_auth_api.py
def test_register_user_integration():
    response = test_client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### 2. **Testes de Serviços** (`tests/services/`)
- **Objetivo**: Testar lógica de negócio isoladamente
- **Mocking**: Banco de dados é mockado usando MagicMock
- **Velocidade**: Muito rápida
- **Cobertura**: Lógica de negócio pura

```python
# Exemplo: test_auth_service.py
async def test_create_user():
    db_session = MagicMock(spec=AsyncSession)
    auth_service = AuthService(db_session)
    user = await auth_service.create_user(user_data)
    assert user.email == "test@example.com"
```

## 🚀 Como Executar os Testes

### Todos os testes
```bash
pytest
```

### Apenas testes de API
```bash
pytest tests/api/
```

### Apenas testes de serviços
```bash
pytest tests/services/
```

### Teste específico com verbose
```bash
pytest tests/services/test_auth_service.py -v
```

### Com cobertura de código
```bash
pytest --cov=app tests/
```

## 📁 Estrutura dos Testes

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
└── conftest.py            # Configurações compartilhadas
```

## 🔧 Configuração

O projeto usa `pytest.ini` para configuração automática:
- **pythonpath**: Configurado para encontrar o módulo `app`
- **testpaths**: Diretório padrão dos testes
- **addopts**: Opções padrão como verbose

## ✅ Vantagens desta Abordagem

1. **Velocidade**: Testes executam em milissegundos
2. **Confiabilidade**: Sem problemas de estado do banco
3. **Manutenibilidade**: Fácil adicionar novos testes
4. **CI/CD**: Sem dependências externas
5. **Debugging**: Pontos de falha claros

## 🛠️ Estratégia de Mocking

### O que é mockado:
- **Sessão do Banco**: Operações `AsyncSession` (add, commit, refresh, execute)
- **Serviços Externos**: Chamadas para Yahoo Finance API
- **Autenticação**: Verificação de tokens JWT
- **Construtores de Modelos**: `User()`, `Client()`, etc.

### O que NÃO é mockado:
- **Lógica de Negócio**: Métodos da camada de serviço
- **Validação de Dados**: Schemas Pydantic
- **Camada HTTP**: Tratamento de requisições/respostas FastAPI

## 📝 Exemplos de Testes

### Teste de API
```python
@pytest.mark.asyncio
async def test_register_user_integration(test_client):
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    with patch('app.api.auth.AuthService') as mock_auth_service_class:
        mock_auth_service = AsyncMock()
        mock_auth_service_class.return_value = mock_auth_service
        mock_auth_service.get_user_by_email.return_value = None
        mock_auth_service.create_user.return_value = mock_user
        
        response = test_client.post("/auth/register", json=user_data)
        
        assert response.status_code == 200
        assert "access_token" in response.json()
```

### Teste de Serviço
```python
@pytest.mark.asyncio
async def test_create_user():
    db_session = MagicMock(spec=AsyncSession)
    auth_service = AuthService(db_session)
    
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123"
    )
    
    mock_user = User()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    
    with patch('app.services.auth_service.User') as mock_user_class:
        mock_user_class.return_value = mock_user
        
        user = await auth_service.create_user(user_data)
    
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    
    assert user.email == "test@example.com"
    assert user.id == 1
```

## 🔍 Troubleshooting

### Problemas Comuns:

1. **Erro de Import**: Verifique se o `pytest.ini` está configurado
2. **Mock não funciona**: Confirme que está fazendo patch do caminho correto
3. **Falha de autenticação**: Certifique-se que `get_current_user` está mockado
4. **Erro de banco**: Verifique se `AsyncSession` está mockado corretamente

### Dicas de Debug:

1. Use `pytest -v` para saída verbosa
2. Use `pytest --pdb` para entrar no debugger em falhas
3. Adicione `print()` nos testes para debug de chamadas mock
4. Verifique histórico de chamadas com `mock_service.method_name.call_args_list`