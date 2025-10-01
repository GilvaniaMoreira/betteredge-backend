import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserLogin
from app.models.user import User


class TestAuthIntegration:
    """True integration tests for authentication - tests service layer with mocked dependencies"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def auth_service(self, mock_db_session):
        """Create auth service with mocked database"""
        return AuthService(mock_db_session)
    
    @pytest.fixture
    def test_client(self, mock_db_session):
        """Create test client with mocked database dependency"""
        def override_get_db():
            return mock_db_session
        
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_register_user_integration(self, test_client, mock_db_session, auth_service):
        """Integration test: Register user through API with mocked database"""
        # Setup mock behavior
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None  # No existing user
        mock_db_session.add = AsyncMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Mock the auth service methods
        with patch('app.api.auth.AuthService') as mock_auth_service_class:
            mock_auth_service = AsyncMock()
            mock_auth_service_class.return_value = mock_auth_service
            
            # Mock successful user creation
            mock_user = AsyncMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.is_active = True
            mock_user.password = "hashed_password"
            mock_user.created_at = "2024-01-01T00:00:00"
            mock_user.updated_at = "2024-01-01T00:00:00"
            
            mock_auth_service.get_user_by_email.return_value = None  # User doesn't exist
            mock_auth_service.create_user.return_value = mock_user
            
            # Make API call
            user_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = test_client.post("/auth/register", json=user_data)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["is_active"] is True
            assert "id" in data
            assert "password" not in data
            
            # Verify service was called correctly
            mock_auth_service.get_user_by_email.assert_called_once_with("test@example.com")
            mock_auth_service.create_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email_integration(self, test_client, mock_db_session):
        """Integration test: Register with duplicate email through API"""
        with patch('app.api.auth.AuthService') as mock_auth_service_class:
            mock_auth_service = AsyncMock()
            mock_auth_service_class.return_value = mock_auth_service
            
            # Mock existing user found
            existing_user = AsyncMock()
            existing_user.email = "test@example.com"
            mock_auth_service.get_user_by_email.return_value = existing_user
            
            user_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = test_client.post("/auth/register", json=user_data)
            
            # Verify error response
            assert response.status_code == 400
            assert "Email already registered" in response.json()["detail"]
            
            # Verify service was called but create_user was not
            mock_auth_service.get_user_by_email.assert_called_once_with("test@example.com")
            mock_auth_service.create_user.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_login_user_integration(self, test_client, mock_db_session):
        """Integration test: Login user through API with mocked services"""
        with patch('app.api.auth.AuthService') as mock_auth_service_class:
            mock_auth_service = AsyncMock()
            mock_auth_service_class.return_value = mock_auth_service
            
            # Mock successful authentication
            mock_user = AsyncMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.is_active = True
            
            mock_auth_service.authenticate_user.return_value = mock_user
            mock_auth_service.create_access_token.return_value = "fake_jwt_token"
            
            user_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = test_client.post("/auth/login", json=user_data)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert data["access_token"] == "fake_jwt_token"
            
            # Verify service calls
            mock_auth_service.authenticate_user.assert_called_once()
            mock_auth_service.create_access_token.assert_called_once_with(mock_user)
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials_integration(self, test_client, mock_db_session):
        """Integration test: Login with invalid credentials through API"""
        with patch('app.api.auth.AuthService') as mock_auth_service_class:
            mock_auth_service = AsyncMock()
            mock_auth_service_class.return_value = mock_auth_service
            
            # Mock authentication failure
            mock_auth_service.authenticate_user.return_value = None
            
            user_data = {
                "email": "test@example.com",
                "password": "wrongpassword"
            }
            
            response = test_client.post("/auth/login", json=user_data)
            
            # Verify error response
            assert response.status_code == 401
            assert "Incorrect email or password" in response.json()["detail"]
            
            # Verify service was called but token creation was not
            mock_auth_service.authenticate_user.assert_called_once()
            mock_auth_service.create_access_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_current_user_integration(self, test_client, mock_db_session):
        """Integration test: Get current user through API with mocked authentication"""
        # Mock authenticated user
        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.created_at = "2024-01-01T00:00:00"
        mock_user.updated_at = "2024-01-01T00:00:00"
        
        # Override the get_current_user dependency
        def mock_get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user_override
        
        try:
            response = test_client.get("/auth/me", headers={"Authorization": "Bearer fake_token"})
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["id"] == 1
            assert "password" not in data
        finally:
            # Clean up the override
            app.dependency_overrides.pop(get_current_user, None)
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized_integration(self, test_client):
        """Integration test: Get current user without authentication"""
        response = test_client.get("/auth/me")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth headers
