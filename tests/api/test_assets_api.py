import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.asset_service import AssetService
from app.services.auth_service import AuthService
from app.schemas.asset import AssetCreate
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
    async def test_asset_endpoints_unauthorized_integration(self, test_client):
        """Integration test: All asset endpoints require authentication"""
        asset_data = {"name": "Test Asset", "ticker": "TEST", "exchange": "NASDAQ", "currency": "USD", "current_price": 100.0, "sector": "Test", "industry": "Test", "market_cap": 1000000}
        
        # Test all endpoints without authentication
        endpoints = [
            ("GET", "/assets/"),
            ("POST", "/assets/", asset_data),
            ("GET", "/assets/1"),
            ("GET", "/assets/yahoo/search?query=test&limit=10"),
            ("GET", "/assets/yahoo/details/AAPL")
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

    @pytest.mark.asyncio
    async def test_search_yahoo_assets_by_name_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Search Yahoo Finance assets by name through API (simplified results)"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock simplified search results
                mock_search_results = [
                    {
                        "ticker": "AAPL",
                        "name": "Apple Inc",
                        "exchange": "NASDAQ"
                    },
                    {
                        "ticker": "AMZN",
                        "name": "Amazon.com Inc",
                        "exchange": "NASDAQ"
                    }
                ]
                
                mock_asset_service.search_yahoo_assets_by_name.return_value = mock_search_results
                
                # Test search with query parameter
                response = test_client.get("/assets/yahoo/search?query=apple&limit=5", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 2
                
                # Verify first result (simplified)
                assert data[0]["ticker"] == "AAPL"
                assert data[0]["name"] == "Apple Inc"
                assert data[0]["exchange"] == "NASDAQ"
                
                # Verify second result (simplified)
                assert data[1]["ticker"] == "AMZN"
                assert data[1]["name"] == "Amazon.com Inc"
                assert data[1]["exchange"] == "NASDAQ"
                
                # Verify service was called with correct parameters
                mock_asset_service.search_yahoo_assets_by_name.assert_called_once_with("apple", 5)
        finally:
            self._cleanup_auth_override()

    @pytest.mark.asyncio
    async def test_search_yahoo_assets_empty_results_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Search Yahoo Finance assets returns empty list when no results"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock empty search results
                mock_asset_service.search_yahoo_assets_by_name.return_value = []
                
                response = test_client.get("/assets/yahoo/search?query=nonexistent&limit=10", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 0
                
                # Verify service was called
                mock_asset_service.search_yahoo_assets_by_name.assert_called_once_with("nonexistent", 10)
        finally:
            self._cleanup_auth_override()

    @pytest.mark.asyncio
    async def test_search_yahoo_assets_validation_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Search Yahoo Finance assets validates query parameters"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            # Test with empty query (should fail validation)
            response = test_client.get("/assets/yahoo/search?query=&limit=10", headers={"Authorization": "Bearer fake_token"})
            assert response.status_code == 422  # Validation error
            
            # Test with invalid limit (should fail validation)
            response = test_client.get("/assets/yahoo/search?query=apple&limit=0", headers={"Authorization": "Bearer fake_token"})
            assert response.status_code == 422  # Validation error
            
            # Test with limit too high (should fail validation)
            response = test_client.get("/assets/yahoo/search?query=apple&limit=25", headers={"Authorization": "Bearer fake_token"})
            assert response.status_code == 422  # Validation error
            
        finally:
            self._cleanup_auth_override()

    @pytest.mark.asyncio
    async def test_search_yahoo_assets_unauthorized_integration(self, test_client):
        """Integration test: Search Yahoo Finance assets requires authentication"""
        # Test without authentication
        response = test_client.get("/assets/yahoo/search?query=apple&limit=10")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth headers

    @pytest.mark.asyncio
    async def test_get_yahoo_asset_details_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get Yahoo Finance asset details through API"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock detailed asset data
                mock_asset_details = {
                    "ticker": "AAPL",
                    "name": "Apple Inc",
                    "exchange": "NASDAQ",
                    "currency": "USD",
                    "current_price": 150.0,
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "market_cap": 3000000000000,
                    "volume": 1000000,
                    "pe_ratio": 25.0,
                    "dividend_yield": 0.5,
                    "last_updated": "2024-01-01T00:00:00"
                }
                
                mock_asset_service.get_yahoo_asset_details.return_value = mock_asset_details
                
                # Test get details
                response = test_client.get("/assets/yahoo/details/AAPL", headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                # Verify detailed result
                assert data["ticker"] == "AAPL"
                assert data["name"] == "Apple Inc"
                assert data["exchange"] == "NASDAQ"
                assert data["currency"] == "USD"
                assert data["current_price"] == 150.0
                assert data["sector"] == "Technology"
                assert data["industry"] == "Consumer Electronics"
                assert data["market_cap"] == 3000000000000
                assert data["volume"] == 1000000
                assert data["pe_ratio"] == 25.0
                assert data["dividend_yield"] == 0.5
                
                # Verify service was called with correct parameters
                mock_asset_service.get_yahoo_asset_details.assert_called_once_with("AAPL")
        finally:
            self._cleanup_auth_override()

    @pytest.mark.asyncio
    async def test_get_yahoo_asset_details_not_found_integration(self, test_client, mock_db_session, mock_auth_user):
        """Integration test: Get Yahoo Finance asset details returns 404 when not found"""
        self._setup_auth_override(mock_auth_user)
        
        try:
            with patch('app.api.assets.AssetService') as mock_asset_service_class:
                mock_asset_service = AsyncMock()
                mock_asset_service_class.return_value = mock_asset_service
                
                # Mock no details found
                mock_asset_service.get_yahoo_asset_details.return_value = None
                
                # Test get details for non-existent ticker
                response = test_client.get("/assets/yahoo/details/INVALID", headers={"Authorization": "Bearer fake_token"})
                
                # Verify error response
                assert response.status_code == 404
                assert "Asset not found or unable to fetch details" in response.json()["detail"]
                
                # Verify service was called
                mock_asset_service.get_yahoo_asset_details.assert_called_once_with("INVALID")
        finally:
            self._cleanup_auth_override()

    @pytest.mark.asyncio
    async def test_get_yahoo_asset_details_unauthorized_integration(self, test_client):
        """Integration test: Get Yahoo Finance asset details requires authentication"""
        # Test without authentication
        response = test_client.get("/assets/yahoo/details/AAPL")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth headers
