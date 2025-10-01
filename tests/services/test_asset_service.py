"""Simple asset service tests using MagicMock"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.asset_service import AssetService
from app.schemas.asset import AssetCreate, AssetSearchRequest
from app.models.asset import Asset


@pytest.mark.asyncio
async def test_create_asset():
    """Test creating a new asset"""
    db_session = MagicMock(spec=AsyncSession)
    asset_service = AssetService(db_session)
    
    asset_data = AssetCreate(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD"
    )
    
    # Mock asset object
    mock_asset = Asset()
    mock_asset.id = 1
    mock_asset.ticker = "AAPL"
    mock_asset.name = "Apple Inc."
    mock_asset.exchange = "NASDAQ"
    mock_asset.currency = "USD"
    
    with patch('app.services.asset_service.Asset') as mock_asset_class:
        mock_asset_class.return_value = mock_asset
        
        asset = await asset_service.create_asset(asset_data)
    
    # Verify database operations
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()
    
    # Verify result
    assert asset.ticker == "AAPL"
    assert asset.name == "Apple Inc."
    assert asset.exchange == "NASDAQ"
    assert asset.currency == "USD"
    assert asset.id == 1


@pytest.mark.asyncio
async def test_get_asset_by_id():
    """Test getting asset by ID"""
    db_session = MagicMock(spec=AsyncSession)
    asset_service = AssetService(db_session)
    
    # Mock asset object
    mock_asset = Asset()
    mock_asset.id = 1
    mock_asset.ticker = "AAPL"
    mock_asset.name = "Apple Inc."
    mock_asset.exchange = "NASDAQ"
    mock_asset.currency = "USD"
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: mock_asset
    db_session.execute.return_value = mock_result
    
    asset = await asset_service.get_asset(1)
    
    # Verify database query was called
    db_session.execute.assert_called_once()
    
    # Verify result
    assert asset.ticker == "AAPL"
    assert asset.name == "Apple Inc."
    assert asset.id == 1


@pytest.mark.asyncio
async def test_get_asset_by_ticker():
    """Test getting asset by ticker"""
    db_session = MagicMock(spec=AsyncSession)
    asset_service = AssetService(db_session)
    
    # Mock asset object
    mock_asset = Asset()
    mock_asset.id = 1
    mock_asset.ticker = "AAPL"
    mock_asset.name = "Apple Inc."
    mock_asset.exchange = "NASDAQ"
    mock_asset.currency = "USD"
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: mock_asset
    db_session.execute.return_value = mock_result
    
    asset = await asset_service.get_asset_by_ticker("AAPL")
    
    # Verify database query was called
    db_session.execute.assert_called_once()
    
    # Verify result
    assert asset.ticker == "AAPL"
    assert asset.name == "Apple Inc."
    assert asset.id == 1


# Pagination tests are complex to mock properly, keeping only basic tests for now
