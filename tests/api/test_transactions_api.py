import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.transaction_service import TransactionService
from app.services.client_service import ClientService
from app.schemas.transaction import TransactionCreate
from app.models.user import User


class TestTransactionsIntegration:
    """True integration tests for transactions API - tests service layer with mocked dependencies"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def test_client(self, mock_db_session):
        """Create test client with mocked database dependency"""
        def override_get_db():
            return mock_db_session
        
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user"""
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        return mock_user
    
    def _setup_auth_override(self, mock_user):
        """Helper method to set up authentication override"""
        def mock_get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user_override
    
    def _cleanup_auth_override(self):
        """Helper method to clean up authentication override"""
        app.dependency_overrides.pop(get_current_user, None)
    
    @pytest.mark.asyncio
    async def test_create_transaction_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Create transaction through API with mocked services"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.transactions.TransactionService') as mock_transaction_service_class, \
                 patch('app.api.transactions.ClientService') as mock_client_service_class:
                
                mock_transaction_service = AsyncMock()
                mock_transaction_service_class.return_value = mock_transaction_service
                
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock client exists
                mock_client = AsyncMock()
                mock_client.id = 1
                mock_client.name = "Test Client"
                mock_client.email = "client@example.com"
                
                mock_client_service.get_client.return_value = mock_client
                
                # Mock successful transaction creation
                mock_transaction = AsyncMock()
                mock_transaction.id = 1
                mock_transaction.client_id = 1
                mock_transaction.amount = 1000.0
                mock_transaction.type = "deposit"  # Use 'type' not 'transaction_type'
                mock_transaction.note = "Test deposit"  # Use 'note' not 'description'
                mock_transaction.date = "2024-01-01T00:00:00"  # Use 'date' not 'transaction_date'
                mock_transaction.created_at = "2024-01-01T00:00:00"
                mock_transaction.client = mock_client
                
                mock_transaction_service.create_transaction.return_value = mock_transaction
                
                transaction_data = {
                    "client_id": 1,
                    "amount": 1000.0,
                    "type": "deposit",
                    "note": "Test deposit",
                    "date": "2024-01-01T00:00:00"
                }
                
                response = test_client.post("/transactions/", json=transaction_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["client_id"] == 1
                assert data["amount"] == 1000.0
                assert data["type"] == "deposit"
                assert "id" in data
                
                # Verify service was called correctly
                mock_transaction_service.create_transaction.assert_called_once()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_create_transaction_client_not_found_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Create transaction with non-existent client"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.transactions.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock client not found
                mock_client_service.get_client.return_value = None
                
                transaction_data = {
                    "client_id": 999,
                    "amount": 1000.0,
                    "type": "deposit",
                    "note": "Test deposit",
                    "date": "2024-01-01T00:00:00"
                }
                
                response = test_client.post("/transactions/", json=transaction_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify error response
                assert response.status_code == 404
                assert "Client not found" in response.json()["detail"]
                
                # Verify service was called but create_transaction was not
                mock_client_service.get_client.assert_called_once_with(999)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_transactions_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get transactions list through API with mocked services"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.transactions.TransactionService') as mock_transaction_service_class:
                mock_transaction_service = AsyncMock()
                mock_transaction_service_class.return_value = mock_transaction_service
                
                # Mock transactions list response
                mock_transaction1 = AsyncMock()
                mock_transaction1.id = 1
                mock_transaction1.client_id = 1
                mock_transaction1.amount = 1000.0
                mock_transaction1.type = "deposit"
                mock_transaction1.note = "Test deposit"
                mock_transaction1.date = "2024-01-01T00:00:00"
                mock_transaction1.created_at = "2024-01-01T00:00:00"
                
                # Create proper client mock
                mock_client1 = AsyncMock()
                mock_client1.id = 1
                mock_client1.name = "Client 1"
                mock_client1.email = "client1@example.com"
                
                mock_transaction1.client = mock_client1
                
                mock_transaction2 = AsyncMock()
                mock_transaction2.id = 2
                mock_transaction2.client_id = 2
                mock_transaction2.amount = 500.0
                mock_transaction2.type = "withdrawal"
                mock_transaction2.note = "Test withdrawal"
                mock_transaction2.date = "2024-01-01T00:00:00"
                mock_transaction2.created_at = "2024-01-01T00:00:00"
                
                # Create proper client mock
                mock_client2 = AsyncMock()
                mock_client2.id = 2
                mock_client2.name = "Client 2"
                mock_client2.email = "client2@example.com"
                
                mock_transaction2.client = mock_client2
                
                mock_transactions = [mock_transaction1, mock_transaction2]
                mock_transaction_service.get_transactions.return_value = (mock_transactions, 2)
                
                response = test_client.get("/transactions/", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "total" in data
                assert data["total"] == 2
                assert len(data["items"]) == 2
                
                # Verify service was called
                mock_transaction_service.get_transactions.assert_called_once()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_transaction_by_id_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get transaction by ID through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.transactions.TransactionService') as mock_transaction_service_class:
                mock_transaction_service = AsyncMock()
                mock_transaction_service_class.return_value = mock_transaction_service
                
                # Mock transaction found
                mock_transaction = AsyncMock()
                mock_transaction.id = 1
                mock_transaction.client_id = 1
                mock_transaction.amount = 1000.0
                mock_transaction.type = "deposit"
                mock_transaction.note = "Test deposit"
                mock_transaction.date = "2024-01-01T00:00:00"
                mock_transaction.created_at = "2024-01-01T00:00:00"
                
                # Create proper client mock
                mock_client = AsyncMock()
                mock_client.id = 1
                mock_client.name = "Test Client"
                mock_client.email = "client@example.com"
                
                mock_transaction.client = mock_client
                
                mock_transaction_service.get_transaction.return_value = mock_transaction
                
                response = test_client.get("/transactions/1", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["client_id"] == 1
                assert data["amount"] == 1000.0
                assert data["type"] == "deposit"
                assert data["id"] == 1
                
                # Verify service was called
                mock_transaction_service.get_transaction.assert_called_once_with(1)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_transaction_endpoints_unauthorized_integration(self, test_client):
        """Integration test: All transaction endpoints require authentication"""
        transaction_data = {
            "client_id": 1,
            "amount": 1000.0,
            "type": "deposit",
            "note": "Test deposit",
            "date": "2024-01-01T00:00:00"
        }
        
        # Test all endpoints without authentication
        endpoints = [
            ("GET", "/transactions/"),
            ("POST", "/transactions/", transaction_data),
            ("GET", "/transactions/1"),
            ("PUT", "/transactions/1"),
            ("DELETE", "/transactions/1")
        ]
        
        for method, url, *data in endpoints:
            if method == "GET":
                response = test_client.get(url)
            elif method == "POST":
                response = test_client.post(url, json=data[0])
            elif method == "PUT":
                response = test_client.put(url)
            elif method == "DELETE":
                response = test_client.delete(url)
            
            assert response.status_code == 403  # FastAPI returns 403 for missing auth headers
