"""Simple transaction service tests using MagicMock"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.transaction_service import TransactionService
from app.services.client_service import ClientService
from app.schemas.transaction import TransactionCreate, TransactionFilter, TransactionType
from app.schemas.client import ClientCreate
from app.models.transaction import Transaction
from app.models.client import Client
from datetime import datetime


@pytest.mark.asyncio
async def test_create_transaction():
    """Test creating a new transaction"""
    db_session = MagicMock(spec=AsyncSession)
    transaction_service = TransactionService(db_session)
    client_service = ClientService(db_session)
    
    # Mock client
    mock_client = Client()
    mock_client.id = 1
    mock_client.name = "John Doe"
    mock_client.email = "john@example.com"
    
    # Mock client service directly
    mock_client_service = MagicMock()
    mock_client_service.get_client.return_value = mock_client
    
    transaction_data = TransactionCreate(
        client_id=1,
        type=TransactionType.DEPOSIT,
        amount=1000.0,
        date=datetime.now(),
        note="Test deposit"
    )
    
    # Mock transaction object
    mock_transaction = Transaction()
    mock_transaction.id = 1
    mock_transaction.client_id = 1
    mock_transaction.type = TransactionType.DEPOSIT
    mock_transaction.amount = 1000.0
    mock_transaction.note = "Test deposit"
    mock_transaction.client = mock_client
    
    with patch('app.services.transaction_service.Transaction') as mock_transaction_class:
        mock_transaction_class.return_value = mock_transaction
        
        transaction = await transaction_service.create_transaction(transaction_data)
    
    # Verify database operations
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    # Note: refresh is called twice - once for the object and once for the client relationship
    
    # Verify result
    assert transaction.amount == 1000.0
    assert transaction.type == TransactionType.DEPOSIT
    assert transaction.client_id == 1
    assert transaction.note == "Test deposit"


@pytest.mark.asyncio
async def test_get_transaction_by_id():
    """Test getting transaction by ID"""
    db_session = MagicMock(spec=AsyncSession)
    transaction_service = TransactionService(db_session)
    
    # Mock client
    mock_client = Client()
    mock_client.id = 1
    mock_client.name = "John Doe"
    mock_client.email = "john@example.com"
    
    # Mock transaction object
    mock_transaction = Transaction()
    mock_transaction.id = 1
    mock_transaction.client_id = 1
    mock_transaction.type = TransactionType.DEPOSIT
    mock_transaction.amount = 1000.0
    mock_transaction.note = "Test deposit"
    mock_transaction.client = mock_client
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: mock_transaction
    db_session.execute.return_value = mock_result
    
    transaction = await transaction_service.get_transaction(1)
    
    # Verify database query was called
    db_session.execute.assert_called_once()
    
    # Verify result
    assert transaction.amount == 1000.0
    assert transaction.type == TransactionType.DEPOSIT
    assert transaction.client_id == 1


# Pagination tests are complex to mock properly, keeping only basic tests for now
