"""Simple auth service tests using MagicMock"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserLogin
from app.models.user import User


@pytest.mark.asyncio
async def test_create_user():
    """Test creating a new user"""
    db_session = MagicMock(spec=AsyncSession)
    auth_service = AuthService(db_session)
    
    user_data = UserCreate(
        email="test@example.com",
        password="testpassword123"
    )
    
    # Mock user object
    mock_user = User()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.password = "hashed_password_123"
    
    with patch('app.services.auth_service.get_password_hash') as mock_hash, \
         patch('app.services.auth_service.User') as mock_user_class:
        
        mock_hash.return_value = "hashed_password_123"
        mock_user_class.return_value = mock_user
        
        user = await auth_service.create_user(user_data)
    
    # Verify database operations
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()
    
    # Verify result
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.id == 1


@pytest.mark.asyncio
async def test_get_user_by_email():
    """Test getting user by email"""
    db_session = MagicMock(spec=AsyncSession)
    auth_service = AuthService(db_session)
    
    # Mock user object
    mock_user = User()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: mock_user
    db_session.execute.return_value = mock_result
    
    user = await auth_service.get_user_by_email("test@example.com")
    
    # Verify database query was called
    db_session.execute.assert_called_once()
    
    # Verify result
    assert user.email == "test@example.com"
    assert user.id == 1


@pytest.mark.asyncio
async def test_authenticate_user_success():
    """Test successful user authentication"""
    db_session = MagicMock(spec=AsyncSession)
    auth_service = AuthService(db_session)
    
    # Mock user object
    mock_user = User()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.password = "hashed_password_123"
    mock_user.is_active = True
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: mock_user
    db_session.execute.return_value = mock_result
    
    # Mock password verification
    with patch('app.services.auth_service.verify_password') as mock_verify:
        mock_verify.return_value = True
        
        login_data = UserLogin(
            email="test@example.com",
            password="testpassword123"
        )
        
        user = await auth_service.authenticate_user(login_data)
    
    # Verify result
    assert user.email == "test@example.com"
    assert user.id == 1


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password():
    """Test authentication with wrong password"""
    db_session = MagicMock(spec=AsyncSession)
    auth_service = AuthService(db_session)
    
    # Mock user object
    mock_user = User()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.password = "hashed_password_123"
    mock_user.is_active = True
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = lambda: mock_user
    db_session.execute.return_value = mock_result
    
    # Mock password verification to return False
    with patch('app.services.auth_service.verify_password') as mock_verify:
        mock_verify.return_value = False
        
        login_data = UserLogin(
            email="test@example.com",
            password="wrongpassword"
        )
        
        user = await auth_service.authenticate_user(login_data)
    
    # Verify result
    assert user is None
