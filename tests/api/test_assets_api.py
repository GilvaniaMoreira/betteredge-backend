import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.asset_service import AssetService
from app.services.auth_service import AuthService
from app.schemas.asset import AssetCreate, AssetSearchRequest
from app.models.user import User


class TestAssetsIntegration:
    """True integration tests for assets API - tests service layer with mocked dependencies"""
    
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
    async def test_create_asset_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Create asset through API with mocked services"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock no existing asset (for duplicate check)
                mock_asset_service.get_asset_by_ticker.return_value = None
                
                # Mock successful asset creation
                mock_asset = AsyncMock()
                mock_asset.id = 1
                mock_asset.name = "Apple Inc"
                mock_asset.ticker = "AAPL"
                mock_asset.exchange = "NASDAQ"
                mock_asset.currency = "USD"
                mock_asset.current_price = 150.0
                mock_asset.sector = "Technology"
                mock_asset.industry = "Consumer Electronics"
                mock_asset.market_cap = 3000000000000
                mock_asset.volume = 1000000
                mock_asset.pe_ratio = 25.0
                mock_asset.dividend_yield = 0.5
                mock_asset.last_updated = "2024-01-01T00:00:00"
                mock_asset.created_at = "2024-01-01T00:00:00"
                
                mock_asset_service.create_asset.return_value = mock_asset
                
                asset_data = {
                    "name": "Apple Inc",
                    "ticker": "AAPL",
                    "exchange": "NASDAQ",
                    "currency": "USD",
                    "current_price": 150.0,
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "market_cap": 3000000000000,
                    "volume": 1000000,
                    "pe_ratio": 25.0,
                    "dividend_yield": 0.5
                }
                
                response = test_client.post("/assets/", json=asset_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "Apple Inc"
                assert data["ticker"] == "AAPL"
                assert data["sector"] == "Technology"
                assert data["exchange"] == "NASDAQ"
                assert data["currency"] == "USD"
                assert "id" in data
                
                # Verify service was called correctly
                mock_asset_service.create_asset.assert_called_once()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_create_asset_duplicate_ticker_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Create asset with duplicate ticker through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock existing asset found
                existing_asset = AsyncMock()
                existing_asset.ticker = "AAPL"
                mock_asset_service.get_asset_by_ticker.return_value = existing_asset
                
                asset_data = {
                    "name": "Apple Inc",
                    "ticker": "AAPL",
                    "exchange": "NASDAQ",
                    "currency": "USD",
                    "current_price": 150.0,
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "market_cap": 3000000000000
                }
                
                response = test_client.post("/assets/", json=asset_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify error response
                assert response.status_code == 400
                assert "Asset with this ticker already exists" in response.json()["detail"]
                
                # Verify service was called but create_asset was not
                mock_asset_service.get_asset_by_ticker.assert_called_once_with("AAPL")
                mock_asset_service.create_asset.assert_not_called()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_assets_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get assets list through API with mocked services"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock assets list response - create proper mock objects
                mock_asset1 = AsyncMock()
                mock_asset1.id = 1
                mock_asset1.name = "Apple Inc"
                mock_asset1.ticker = "AAPL"
                mock_asset1.exchange = "NASDAQ"
                mock_asset1.currency = "USD"
                mock_asset1.current_price = 150.0
                mock_asset1.sector = "Technology"
                mock_asset1.industry = "Consumer Electronics"
                mock_asset1.market_cap = 3000000000000
                mock_asset1.volume = 1000000
                mock_asset1.pe_ratio = 25.0
                mock_asset1.dividend_yield = 0.5
                mock_asset1.last_updated = "2024-01-01T00:00:00"
                mock_asset1.created_at = "2024-01-01T00:00:00"
                
                mock_asset2 = AsyncMock()
                mock_asset2.id = 2
                mock_asset2.name = "Microsoft Corp"
                mock_asset2.ticker = "MSFT"
                mock_asset2.exchange = "NASDAQ"
                mock_asset2.currency = "USD"
                mock_asset2.current_price = 300.0
                mock_asset2.sector = "Technology"
                mock_asset2.industry = "Software"
                mock_asset2.market_cap = 2800000000000
                mock_asset2.volume = 2000000
                mock_asset2.pe_ratio = 30.0
                mock_asset2.dividend_yield = 0.8
                mock_asset2.last_updated = "2024-01-01T00:00:00"
                mock_asset2.created_at = "2024-01-01T00:00:00"
                
                mock_assets = [mock_asset1, mock_asset2]
                mock_asset_service.get_assets.return_value = (mock_assets, 2)
                
                response = test_client.get("/assets/", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "total" in data
                assert data["total"] == 2
                assert len(data["items"]) == 2
                
                # Verify service was called
                mock_asset_service.get_assets.assert_called_once()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_assets_with_pagination_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get assets with pagination through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock paginated response
                mock_asset = AsyncMock()
                mock_asset.id = 1
                mock_asset.name = "Apple Inc"
                mock_asset.ticker = "AAPL"
                mock_asset.exchange = "NASDAQ"
                mock_asset.currency = "USD"
                mock_asset.current_price = 150.0
                mock_asset.sector = "Technology"
                mock_asset.industry = "Consumer Electronics"
                mock_asset.market_cap = 3000000000000
                mock_asset.volume = 1000000
                mock_asset.pe_ratio = 25.0
                mock_asset.dividend_yield = 0.5
                mock_asset.last_updated = "2024-01-01T00:00:00"
                mock_asset.created_at = "2024-01-01T00:00:00"
                
                mock_assets = [mock_asset]
                mock_asset_service.get_assets.return_value = (mock_assets, 5)
                
                response = test_client.get("/assets/?skip=0&limit=1", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert len(data["items"]) == 1
                assert data["total"] == 5
                assert data["page"] == 1
                
                # Verify service was called with pagination parameters
                mock_asset_service.get_assets.assert_called_once_with(0, 1, None)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_assets_with_search_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get assets with search through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock search response
                mock_asset = AsyncMock()
                mock_asset.id = 1
                mock_asset.name = "Apple Inc"
                mock_asset.ticker = "AAPL"
                mock_asset.exchange = "NASDAQ"
                mock_asset.currency = "USD"
                mock_asset.current_price = 150.0
                mock_asset.sector = "Technology"
                mock_asset.industry = "Consumer Electronics"
                mock_asset.market_cap = 3000000000000
                mock_asset.volume = 1000000
                mock_asset.pe_ratio = 25.0
                mock_asset.dividend_yield = 0.5
                mock_asset.last_updated = "2024-01-01T00:00:00"
                mock_asset.created_at = "2024-01-01T00:00:00"
                
                mock_assets = [mock_asset]
                mock_asset_service.get_assets.return_value = (mock_assets, 1)
                
                response = test_client.get("/assets/?search=AAPL", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert len(data["items"]) == 1
                assert data["total"] == 1
                
                # Verify service was called with search parameter
                mock_asset_service.get_assets.assert_called_once_with(0, 100, "AAPL")
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_asset_by_id_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get asset by ID through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock asset found
                mock_asset = AsyncMock()
                mock_asset.id = 1
                mock_asset.name = "Apple Inc"
                mock_asset.ticker = "AAPL"
                mock_asset.exchange = "NASDAQ"
                mock_asset.currency = "USD"
                mock_asset.current_price = 150.0
                mock_asset.sector = "Technology"
                mock_asset.industry = "Consumer Electronics"
                mock_asset.market_cap = 3000000000000
                mock_asset.volume = 1000000
                mock_asset.pe_ratio = 25.0
                mock_asset.dividend_yield = 0.5
                mock_asset.last_updated = "2024-01-01T00:00:00"
                mock_asset.created_at = "2024-01-01T00:00:00"
                
                mock_asset_service.get_asset.return_value = mock_asset
                
                response = test_client.get("/assets/1", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "Apple Inc"
                assert data["ticker"] == "AAPL"
                assert data["id"] == 1
                
                # Verify service was called
                mock_asset_service.get_asset.assert_called_once_with(1)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_get_asset_by_id_not_found_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get non-existent asset through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock asset not found
                mock_asset_service.get_asset.return_value = None
                
                response = test_client.get("/assets/999", headers={"Authorization": "Bearer fake_token"})
                
                # Verify error response
                assert response.status_code == 404
                assert "Asset not found" in response.json()["detail"]
                
                # Verify service was called
                mock_asset_service.get_asset.assert_called_once_with(999)
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_search_asset_from_yahoo_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Search asset from Yahoo Finance through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock Yahoo Finance data
                yahoo_data = AsyncMock()
                yahoo_data.ticker = "AAPL"
                yahoo_data.name = "Apple Inc"
                yahoo_data.exchange = "NASDAQ"
                yahoo_data.currency = "USD"
                yahoo_data.current_price = 150.0
                yahoo_data.sector = "Technology"
                yahoo_data.industry = "Consumer Electronics"
                yahoo_data.market_cap = 3000000000000
                yahoo_data.volume = 1000000
                yahoo_data.pe_ratio = 25.0
                yahoo_data.dividend_yield = 0.5
                
                mock_asset_service.fetch_asset_from_yahoo.return_value = yahoo_data
                
                search_data = {"ticker": "AAPL"}
                
                response = test_client.post("/assets/search", json=search_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["ticker"] == "AAPL"
                assert data["name"] == "Apple Inc"
                assert data["current_price"] == 150.0
                
                # Verify service was called
                mock_asset_service.fetch_asset_from_yahoo.assert_called_once_with("AAPL")
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_update_asset_price_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Update asset price through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock updated asset
                updated_asset = AsyncMock()
                updated_asset.id = 1
                updated_asset.name = "Apple Inc"
                updated_asset.ticker = "AAPL"
                updated_asset.exchange = "NASDAQ"
                updated_asset.currency = "USD"
                updated_asset.current_price = 155.0
                updated_asset.sector = "Technology"
                updated_asset.industry = "Consumer Electronics"
                updated_asset.market_cap = 3100000000000
                updated_asset.volume = 1000000
                updated_asset.pe_ratio = 25.0
                updated_asset.dividend_yield = 0.5
                updated_asset.last_updated = "2024-01-01T00:00:00"
                updated_asset.created_at = "2024-01-01T00:00:00"
                
                # Mock the service calls for update_asset_price endpoint
                mock_asset_service.get_asset.return_value = AsyncMock(id=1, ticker="AAPL")  # Mock existing asset
                mock_asset_service.fetch_asset_from_yahoo.return_value = AsyncMock(ticker="AAPL")  # Mock Yahoo data
                mock_asset_service.update_asset_from_yahoo.return_value = updated_asset
                
                response = test_client.put("/assets/1/update-price", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["ticker"] == "AAPL"
                assert data["current_price"] == 155.0
                
                # Verify service calls
                mock_asset_service.get_asset.assert_called_once_with(1)
                mock_asset_service.fetch_asset_from_yahoo.assert_called_once_with("AAPL")
                mock_asset_service.update_asset_from_yahoo.assert_called_once()
        finally:
            self._cleanup_auth_override()
    
    @pytest.mark.asyncio
    async def test_asset_endpoints_unauthorized_integration(self, test_client):
        """Integration test: All asset endpoints require authentication"""
        asset_data = {"name": "Test Asset", "ticker": "TEST", "exchange": "NASDAQ", "currency": "USD", "current_price": 100.0, "sector": "Test", "industry": "Test", "market_cap": 1000000}
        
        # Test all endpoints without authentication
        endpoints = [
            ("GET", "/assets/"),
            ("POST", "/assets/", asset_data),
            ("GET", "/assets/1"),
            ("POST", "/assets/search", {"ticker": "TEST"}),
            ("PUT", "/assets/1/update-price")
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
