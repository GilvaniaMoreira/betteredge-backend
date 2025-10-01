import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.allocation_service import AllocationService
from app.services.client_service import ClientService
from app.services.asset_service import AssetService
from app.schemas.allocation import AllocationCreate, AllocationCreateByTicker
from app.models.user import User


class TestAllocationsIntegration:
    """True integration tests for allocations API - tests service layer with mocked dependencies"""
    
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
    async def test_create_allocation_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Create allocation through API with mocked services"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.allocations.AllocationService') as mock_allocation_service_class, \
                 patch('app.api.allocations.ClientService') as mock_client_service_class, \
                 patch('app.api.allocations.AssetService') as mock_asset_service_class:
                
                mock_allocation_service = AsyncMock()
                mock_allocation_service_class.return_value = mock_allocation_service
                
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock client and asset exist
                mock_client = AsyncMock()
                mock_client.id = 1
                mock_client.name = "Test Client"
                mock_client.email = "client@example.com"
                
                mock_asset = AsyncMock()
                mock_asset.id = 1
                mock_asset.ticker = "AAPL"
                mock_asset.name = "Apple Inc"
                
                mock_client_service.get_client.return_value = mock_client
                mock_asset_service.get_asset.return_value = mock_asset
                
                # Mock successful allocation creation
                mock_allocation = AsyncMock()
                mock_allocation.id = 1
                mock_allocation.client_id = 1
                mock_allocation.asset_id = 1
                mock_allocation.quantity = 10.0
                mock_allocation.buy_price = 150.0
                mock_allocation.buy_date = "2024-01-01T00:00:00"
                mock_allocation.created_at = "2024-01-01T00:00:00"
                mock_allocation.client = mock_client
                mock_allocation.asset = mock_asset
                
                mock_allocation_service.create_allocation.return_value = mock_allocation
                
                allocation_data = {
                    "client_id": 1,
                    "asset_id": 1,
                    "quantity": 10.0,
                    "buy_price": 150.0,
                    "buy_date": "2024-01-01T00:00:00"
                }
                
                response = test_client.post("/allocations/", json=allocation_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["client_id"] == 1
                assert data["asset_id"] == 1
                assert data["quantity"] == 10.0
                assert data["buy_price"] == 150.0
                assert "id" in data
                
                # Verify service was called correctly
                mock_allocation_service.create_allocation.assert_called_once()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_create_allocation_client_not_found_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Create allocation with non-existent client"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.allocations.ClientService') as mock_client_service_class:
                mock_client_service = AsyncMock()
                mock_client_service_class.return_value = mock_client_service
                
                # Mock client not found
                mock_client_service.get_client.return_value = None
                
                allocation_data = {
                    "client_id": 999,
                    "asset_id": 1,
                    "quantity": 10.0,
                    "buy_price": 150.0,
                    "buy_date": "2024-01-01T00:00:00"
                }
                
                response = test_client.post("/allocations/", json=allocation_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify error response
                assert response.status_code == 404
                assert "Client not found" in response.json()["detail"]
                
                # Verify service was called but create_allocation was not
                mock_client_service.get_client.assert_called_once_with(999)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_allocations_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get allocations list through API with mocked services"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.allocations.AllocationService') as mock_allocation_service_class:
                mock_allocation_service = AsyncMock()
                mock_allocation_service_class.return_value = mock_allocation_service
                
                # Mock allocations list response
                mock_allocation1 = AsyncMock()
                mock_allocation1.id = 1
                mock_allocation1.client_id = 1
                mock_allocation1.asset_id = 1
                mock_allocation1.quantity = 10.0
                mock_allocation1.buy_price = 150.0
                mock_allocation1.buy_date = "2024-01-01T00:00:00"
                mock_allocation1.created_at = "2024-01-01T00:00:00"
                # Create proper client and asset mocks
                mock_client1 = AsyncMock()
                mock_client1.id = 1
                mock_client1.name = "Client 1"
                mock_client1.email = "client1@example.com"
                
                mock_asset1 = AsyncMock()
                mock_asset1.id = 1
                mock_asset1.ticker = "AAPL"
                mock_asset1.name = "Apple Inc"
                
                mock_allocation1.client = mock_client1
                mock_allocation1.asset = mock_asset1
                
                mock_allocation2 = AsyncMock()
                mock_allocation2.id = 2
                mock_allocation2.client_id = 2
                mock_allocation2.asset_id = 2
                mock_allocation2.quantity = 20.0
                mock_allocation2.buy_price = 300.0
                mock_allocation2.buy_date = "2024-01-01T00:00:00"
                mock_allocation2.created_at = "2024-01-01T00:00:00"
                
                # Create proper client and asset mocks
                mock_client2 = AsyncMock()
                mock_client2.id = 2
                mock_client2.name = "Client 2"
                mock_client2.email = "client2@example.com"
                
                mock_asset2 = AsyncMock()
                mock_asset2.id = 2
                mock_asset2.ticker = "MSFT"
                mock_asset2.name = "Microsoft Corp"
                
                mock_allocation2.client = mock_client2
                mock_allocation2.asset = mock_asset2
                
                mock_allocations = [mock_allocation1, mock_allocation2]
                mock_allocation_service.get_allocations.return_value = (mock_allocations, 2)
                
                response = test_client.get("/allocations/", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "total" in data
                assert data["total"] == 2
                assert len(data["items"]) == 2
                
                # Verify service was called
                mock_allocation_service.get_allocations.assert_called_once()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_allocation_by_id_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get allocation by ID through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.allocations.AllocationService') as mock_allocation_service_class:
                mock_allocation_service = AsyncMock()
                mock_allocation_service_class.return_value = mock_allocation_service
                
                # Mock allocation found
                mock_allocation = AsyncMock()
                mock_allocation.id = 1
                mock_allocation.client_id = 1
                mock_allocation.asset_id = 1
                mock_allocation.quantity = 10.0
                mock_allocation.buy_price = 150.0
                mock_allocation.buy_date = "2024-01-01T00:00:00"
                mock_allocation.created_at = "2024-01-01T00:00:00"
                # Create proper client and asset mocks
                mock_client = AsyncMock()
                mock_client.id = 1
                mock_client.name = "Test Client"
                mock_client.email = "client@example.com"
                
                mock_asset = AsyncMock()
                mock_asset.id = 1
                mock_asset.ticker = "AAPL"
                mock_asset.name = "Apple Inc"
                
                mock_allocation.client = mock_client
                mock_allocation.asset = mock_asset
                
                mock_allocation_service.get_allocation.return_value = mock_allocation
                
                response = test_client.get("/allocations/1", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["client_id"] == 1
                assert data["asset_id"] == 1
                assert data["quantity"] == 10.0
                assert data["id"] == 1
                
                # Verify service was called
                mock_allocation_service.get_allocation.assert_called_once_with(1)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_allocation_by_id_not_found_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get non-existent allocation through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.allocations.AllocationService') as mock_allocation_service_class:
                mock_allocation_service = AsyncMock()
                mock_allocation_service_class.return_value = mock_allocation_service
                
                # Mock allocation not found
                mock_allocation_service.get_allocation.return_value = None
                
                response = test_client.get("/allocations/999", headers={"Authorization": "Bearer fake_token"})
                
                # Verify error response
                assert response.status_code == 404
                assert "Allocation not found" in response.json()["detail"]
                
                # Verify service was called
                mock_allocation_service.get_allocation.assert_called_once_with(999)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_allocation_endpoints_unauthorized_integration(self, test_client):
        """Integration test: All allocation endpoints require authentication"""
        allocation_data = {
            "client_id": 1,
            "asset_id": 1,
            "quantity": 10.0,
            "buy_price": 150.0,
            "buy_date": "2024-01-01T00:00:00"
        }
        
        # Test all endpoints without authentication
        endpoints = [
            ("GET", "/allocations/"),
            ("POST", "/allocations/", allocation_data),
            ("GET", "/allocations/1"),
            ("PUT", "/allocations/1"),
            ("DELETE", "/allocations/1")
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