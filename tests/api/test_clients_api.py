import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.client_service import ClientService
from app.services.auth_service import AuthService
from app.schemas.client import ClientCreate, ClientUpdate
from app.models.user import User


class TestClientsIntegration:
    """True integration tests for clients API - tests service layer with mocked dependencies"""
    
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
    async def test_create_client_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Create client through API with mocked services"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.clients.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock no existing client (for duplicate check)
                mock_client_service.get_client_by_email.return_value = None
                
                # Mock successful client creation
                mock_client = AsyncMock()
                mock_client.id = 1
                mock_client.name = "John Doe"
                mock_client.email = "john@example.com"
                mock_client.is_active = True
                mock_client.created_at = "2024-01-01T00:00:00"
                mock_client.updated_at = "2024-01-01T00:00:00"
                
                mock_client_service.create_client.return_value = mock_client
                
                client_data = {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "is_active": True
                }
                
                response = test_client.post("/clients/", json=client_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "John Doe"
                assert data["email"] == "john@example.com"
                assert data["is_active"] is True
                assert "id" in data
                
                # Verify service was called correctly
                mock_client_service.create_client.assert_called_once()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_create_client_duplicate_email_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Create client with duplicate email through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.clients.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock existing client found
                existing_client = AsyncMock()
                existing_client.email = "john@example.com"
                mock_client_service.get_client_by_email.return_value = existing_client
                
                client_data = {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "is_active": True
                }
                
                response = test_client.post("/clients/", json=client_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify error response
                assert response.status_code == 400
                assert "Client with this email already exists" in response.json()["detail"]
                
                # Verify service was called but create_client was not
                mock_client_service.get_client_by_email.assert_called_once_with("john@example.com")
                mock_client_service.create_client.assert_not_called()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_clients_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get clients list through API with mocked services"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.clients.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock clients list response - create proper mock objects
                mock_client1 = AsyncMock()
                mock_client1.id = 1
                mock_client1.name = "Client 1"
                mock_client1.email = "client1@example.com"
                mock_client1.is_active = True
                mock_client1.created_at = "2024-01-01T00:00:00"
                mock_client1.updated_at = "2024-01-01T00:00:00"
                
                mock_client2 = AsyncMock()
                mock_client2.id = 2
                mock_client2.name = "Client 2"
                mock_client2.email = "client2@example.com"
                mock_client2.is_active = True
                mock_client2.created_at = "2024-01-01T00:00:00"
                mock_client2.updated_at = "2024-01-01T00:00:00"
                
                mock_clients = [mock_client1, mock_client2]
                mock_client_service.get_clients.return_value = (mock_clients, 2)
                
                response = test_client.get("/clients/", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "total" in data
                assert data["total"] == 2
                assert len(data["items"]) == 2
                
                # Verify service was called
                mock_client_service.get_clients.assert_called_once()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_clients_with_pagination_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get clients with pagination through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.clients.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock paginated response
                mock_client = AsyncMock()
                mock_client.id = 1
                mock_client.name = "Client 1"
                mock_client.email = "client1@example.com"
                mock_client.is_active = True
                mock_client.created_at = "2024-01-01T00:00:00"
                mock_client.updated_at = "2024-01-01T00:00:00"
                
                mock_clients = [mock_client]
                mock_client_service.get_clients.return_value = (mock_clients, 5)
                
                response = test_client.get("/clients/?skip=0&limit=1", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert len(data["items"]) == 1
                assert data["total"] == 5
                assert data["page"] == 1
                
                # Verify service was called with pagination parameters
                mock_client_service.get_clients.assert_called_once_with(0, 1, None, None)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_clients_with_search_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get clients with search through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.clients.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock search response
                mock_client = AsyncMock()
                mock_client.id = 1
                mock_client.name = "John Smith"
                mock_client.email = "john@example.com"
                mock_client.is_active = True
                mock_client.created_at = "2024-01-01T00:00:00"
                mock_client.updated_at = "2024-01-01T00:00:00"
                
                mock_clients = [mock_client]
                mock_client_service.get_clients.return_value = (mock_clients, 1)
                
                response = test_client.get("/clients/?search=John", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert len(data["items"]) == 1
                assert data["total"] == 1
                
                # Verify service was called with search parameter
                mock_client_service.get_clients.assert_called_once_with(0, 100, "John", None)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_client_by_id_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get client by ID through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.clients.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock client found
                mock_client = AsyncMock()
                mock_client.id = 1
                mock_client.name = "John Doe"
                mock_client.email = "john@example.com"
                mock_client.is_active = True
                mock_client.created_at = "2024-01-01T00:00:00"
                mock_client.updated_at = "2024-01-01T00:00:00"
                
                mock_client_service.get_client.return_value = mock_client
                
                response = test_client.get("/clients/1", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "John Doe"
                assert data["email"] == "john@example.com"
                assert data["id"] == 1
                
                # Verify service was called
                mock_client_service.get_client.assert_called_once_with(1)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_client_by_id_not_found_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get non-existent client through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.clients.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock client not found
                mock_client_service.get_client.return_value = None
                
                response = test_client.get("/clients/999", headers={"Authorization": "Bearer fake_token"})
                
                # Verify error response
                assert response.status_code == 404
                assert "Client not found" in response.json()["detail"]
                
                # Verify service was called
                mock_client_service.get_client.assert_called_once_with(999)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_update_client_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Update client through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.clients.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock updated client
                updated_client = AsyncMock()
                updated_client.id = 1
                updated_client.name = "Updated Name"
                updated_client.email = "updated@example.com"
                updated_client.is_active = False
                updated_client.created_at = "2024-01-01T00:00:00"
                updated_client.updated_at = "2024-01-01T00:00:00"
                
                mock_client_service.update_client.return_value = updated_client
                
                update_data = {
                    "name": "Updated Name",
                    "email": "updated@example.com",
                    "is_active": False
                }
                
                response = test_client.put("/clients/1", json=update_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "Updated Name"
                assert data["email"] == "updated@example.com"
                assert data["is_active"] is False
                
                # Verify service calls - FastAPI converts JSON to Pydantic model
                call_args = mock_client_service.update_client.call_args
                assert call_args[0][0] == 1  # First arg is client_id
                assert call_args[0][1].name == "Updated Name"  # Second arg is ClientUpdate model
                assert call_args[0][1].email == "updated@example.com"
                assert call_args[0][1].is_active is False
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_delete_client_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Delete client through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.clients.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock successful deletion
                mock_client_service.delete_client.return_value = True
                
                response = test_client.delete("/clients/1", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "Client deleted successfully"
                
                # Verify service calls
                mock_client_service.delete_client.assert_called_once_with(1)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_client_endpoints_unauthorized_integration(self, test_client):
        """Integration test: All client endpoints require authentication"""
        client_data = {"name": "Test", "email": "test@example.com", "is_active": True}
        
        # Test all endpoints without authentication
        endpoints = [
            ("GET", "/clients/"),
            ("POST", "/clients/", client_data),
            ("GET", "/clients/1"),
            ("PUT", "/clients/1", client_data),
            ("DELETE", "/clients/1")
        ]
        
        for method, url, *data in endpoints:
            if method == "GET":
                response = test_client.get(url)
            elif method == "POST":
                response = test_client.post(url, json=data[0])
            elif method == "PUT":
                response = test_client.put(url, json=data[0])
            elif method == "DELETE":
                response = test_client.delete(url)
            
            assert response.status_code == 403  # FastAPI returns 403 for missing auth headers
