"""Simple client service tests using MagicMock"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.client_service import ClientService
from app.schemas.client import ClientCreate, ClientUpdate
from app.models.client import Client


@pytest.mark.asyncio
async def test_create_client():
    """Test creating a new client"""
    db_session = MagicMock(spec=AsyncSession)
    client_service = ClientService(db_session)
    
    client_data = ClientCreate(
        name="John Doe",
        email="john@example.com",
        is_active=True
    )
    
    # Mock client object
    mock_client = Client()
    mock_client.id = 1
    mock_client.name = "John Doe"
    mock_client.email = "john@example.com"
    mock_client.is_active = True
    
    with patch('app.services.client_service.Client') as mock_client_class:
        mock_client_class.return_value = mock_client
        
        client = await client_service.create_client(client_data)
    
    # Verify database operations
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()
    
    # Verify result
    assert client.name == "John Doe"
    assert client.email == "john@example.com"
    assert client.is_active is True
    assert client.id == 1


@pytest.mark.asyncio
async def test_get_client_by_id():
    """Test getting client by ID"""
    db_session = MagicMock(spec=AsyncSession)
    client_service = ClientService(db_session)
    
    # Mock client object
    mock_client = Client()
    mock_client.id = 1
    mock_client.name = "John Doe"
    mock_client.email = "john@example.com"
    mock_client.is_active = True
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: mock_client
    db_session.execute.return_value = mock_result
    
    client = await client_service.get_client(1)
    
    # Verify database query was called
    db_session.execute.assert_called_once()
    
    # Verify result
    assert client.name == "John Doe"
    assert client.email == "john@example.com"
    assert client.id == 1


@pytest.mark.asyncio
async def test_get_client_by_email():
    """Test getting client by email"""
    db_session = MagicMock(spec=AsyncSession)
    client_service = ClientService(db_session)
    
    # Mock client object
    mock_client = Client()
    mock_client.id = 1
    mock_client.name = "John Doe"
    mock_client.email = "john@example.com"
    mock_client.is_active = True
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: mock_client
    db_session.execute.return_value = mock_result
    
    client = await client_service.get_client_by_email("john@example.com")
    
    # Verify database query was called
    db_session.execute.assert_called_once()
    
    # Verify result
    assert client.name == "John Doe"
    assert client.email == "john@example.com"
    assert client.id == 1


@pytest.mark.asyncio
async def test_update_client():
    """Test updating a client"""
    db_session = MagicMock(spec=AsyncSession)
    client_service = ClientService(db_session)
    
    # Mock existing client
    existing_client = Client()
    existing_client.id = 1
    existing_client.name = "John Doe"
    existing_client.email = "john@example.com"
    existing_client.is_active = True
    
    # Mock updated client
    updated_client = Client()
    updated_client.id = 1
    updated_client.name = "John Updated"
    updated_client.email = "john.updated@example.com"
    updated_client.is_active = False
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: existing_client
    db_session.execute.return_value = mock_result
    
    update_data = ClientUpdate(
        name="John Updated",
        email="john.updated@example.com",
        is_active=False
    )
    
    client = await client_service.update_client(1, update_data)
    
    # Verify database operations
    db_session.execute.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()
    
    # Verify result (the service should return the existing client with updated fields)
    assert client.name == "John Updated"
    assert client.email == "john.updated@example.com"
    assert client.is_active is False
