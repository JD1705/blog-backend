import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status
from pydantic import SecretStr

from services.auth_services import AuthService
from schemas.user import UserCreate, UserLogin
from models.user import User

@pytest.mark.asyncio
async def test_register_user_success():
    """
    Test successful user registration when the email doesn't exist.
    """
    mock_db = AsyncMock()
    mock_db.users.find_one.return_value = None
    mock_db.users.insert_one.return_value = None

    with patch('services.auth_services.db', mock_db):
        auth_service = AuthService()
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password=SecretStr("password123"),
            confirm_password=SecretStr("password123"),
            bio="A test bio"
        )

        new_user = await auth_service.register_user(user_data)

        # Assertions
        mock_db.users.find_one.assert_called_once_with({"email": "test@example.com"})
        mock_db.users.insert_one.assert_called_once()
        
        assert isinstance(new_user, User)
        assert new_user.username == "testuser"
        assert new_user.email == "test@example.com"
        assert new_user.bio == "A test bio"
        assert new_user.hashed_password is not None
        assert new_user.hashed_password != "password123"

@pytest.mark.asyncio
async def test_register_user_already_exists():
    """
    Test registration failure when the user already exists.
    """
    mock_db = AsyncMock()
    mock_db.users.find_one.return_value = {"email": "test@example.com"}

    with patch('services.auth_services.db', mock_db):
        auth_service = AuthService()

        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password=SecretStr("password123"),
            confirm_password=SecretStr("password123")
        )

        with pytest.raises(HTTPException) as excinfo:
            await auth_service.register_user(user_data)

        # Assertions
        assert excinfo.value.status_code == status.HTTP_409_CONFLICT
        assert excinfo.value.detail == "User Already Exist"
        mock_db.users.find_one.assert_called_once_with({"email": "test@example.com"})
        mock_db.users.insert_one.assert_not_called()

@pytest.mark.asyncio
async def test_register_user_password_mismatch():
    """
    Test registration failure due to password mismatch.
    The validation is in the Pydantic model, so we test that.
    """
    with pytest.raises(ValueError) as excinfo:
        UserCreate(
            username="testuser",
            email="test@example.com",
            password=SecretStr("password123"),
            confirm_password=SecretStr("password456")
        )
    assert "Passwords dont match" in str(excinfo.value)

# login tests

@pytest.mark.asyncio
async def test_login_user_success():
    """
    Test successful user login.
    """
    mock_user_id = "60c72b2f9f1b2c001a8e4d3a" # Example ObjectId string
    mock_db_user = {
        "_id": mock_user_id,
        "email": "test@example.com",
        "hashed_password": "hashedpassword123",
        "is_active": True
    }
    mock_db = AsyncMock()
    mock_db.users.find_one.return_value = mock_db_user

    with patch('services.auth_services.db', mock_db), \
         patch('services.auth_services.verify_password', return_value=True) as mock_verify_password, \
         patch('services.auth_services.create_jwt_token', return_value="dummy_jwt_token") as mock_create_jwt_token:
        
        auth_service = AuthService()
        user_login_data = UserLogin(
            email="test@example.com",
            password=SecretStr("password123")
        )

        response = await auth_service.login_user(user_login_data)

        mock_db.users.find_one.assert_called_once_with({"email": "test@example.com"})
        mock_verify_password.assert_called_once_with(SecretStr("password123"), "hashedpassword123")
        mock_create_jwt_token.assert_called_once_with({"sub": mock_user_id})

        assert "access_token" in response
        assert response["access_token"] == "dummy_jwt_token"
        assert response["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_user_incorrect_credentials_no_user():
    """
    Test login failure when user does not exist.
    """
    mock_db = AsyncMock()
    mock_db.users.find_one.return_value = None

    with patch('services.auth_services.db', mock_db):
        auth_service = AuthService()
        user_login_data = UserLogin(
            email="nonexistent@example.com",
            password=SecretStr("password123")
        )

        with pytest.raises(HTTPException) as excinfo:
            await auth_service.login_user(user_login_data)

        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert excinfo.value.detail == "Incorrect Credentials"
        mock_db.users.find_one.assert_called_once_with({"email": "nonexistent@example.com"})

@pytest.mark.asyncio
async def test_login_user_incorrect_credentials_wrong_password():
    """
    Test login failure when password is incorrect.
    """
    mock_db_user = {
        "_id": "60c72b2f9f1b2c001a8e4d3a",
        "email": "test@example.com",
        "hashed_password": "hashedpassword123",
        "is_active": True
    }
    mock_db = AsyncMock()
    mock_db.users.find_one.return_value = mock_db_user

    with patch('services.auth_services.db', mock_db), \
         patch('services.auth_services.verify_password', return_value=False) as mock_verify_password:
        
        auth_service = AuthService()
        user_login_data = UserLogin(
            email="test@example.com",
            password=SecretStr("wrongpassword")
        )

        with pytest.raises(HTTPException) as excinfo:
            await auth_service.login_user(user_login_data)

        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert excinfo.value.detail == "Incorrect Credentials"
        mock_db.users.find_one.assert_called_once_with({"email": "test@example.com"})
        mock_verify_password.assert_called_once_with(SecretStr("wrongpassword"), "hashedpassword123")

@pytest.mark.asyncio
async def test_login_user_deactivated_account():
    """
    Test login failure when the account is deactivated.
    """
    mock_db_user = {
        "_id": "60c72b2f9f1b2c001a8e4d3a",
        "email": "deactivated@example.com",
        "hashed_password": "hashedpassword123",
        "is_active": False # Account is deactivated
    }
    mock_db = AsyncMock()
    mock_db.users.find_one.return_value = mock_db_user

    with patch('services.auth_services.db', mock_db), \
         patch('services.auth_services.verify_password', return_value=True) as mock_verify_password:
        
        auth_service = AuthService()
        user_login_data = UserLogin(
            email="deactivated@example.com",
            password=SecretStr("password123")
        )

        with pytest.raises(HTTPException) as excinfo:
            await auth_service.login_user(user_login_data)

        assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert excinfo.value.detail == "Account is deactivated"
        mock_db.users.find_one.assert_called_once_with({"email": "deactivated@example.com"})
        mock_verify_password.assert_not_called() # No need to verify password if account is deactivated


# logout tests

@pytest.mark.asyncio
async def test_logout_user_success():
    """
    Test successful user logout by blacklisting the token.
    """
    mock_db = AsyncMock()
    # Mock the insert_one call for the token_blacklist collection
    mock_db.token_blacklist.insert_one.return_value = None

    with patch('services.auth_services.db', mock_db):
        auth_service = AuthService()
        token_to_blacklist = "some_jwt_token_string"
        
        result = await auth_service.logout_user(token_to_blacklist)

        # Assertions
        mock_db.token_blacklist.insert_one.assert_called_once()
        assert result is True

        # Verify the inserted document structure (optional, but good for robust tests)
        # The first argument of insert_one is the document
        inserted_doc = mock_db.token_blacklist.insert_one.call_args[0][0]
        assert inserted_doc["token"] == token_to_blacklist
        assert "expires_at" in inserted_doc


# is_blacklisted_token tests

@pytest.mark.asyncio
async def test_is_blacklisted_token_true():
    """
    Test if a token is correctly identified as blacklisted.
    """
    mock_db = AsyncMock()
    mock_db.token_blacklist.find_one.return_value = {"token": "blacklisted_token"}

    with patch('services.auth_services.db', mock_db):
        auth_service = AuthService()
        token_to_check = "blacklisted_token"
        
        result = await auth_service.is_blacklisted_token(token_to_check)

        # Assertions
        mock_db.token_blacklist.find_one.assert_called_once_with({"token": token_to_check})
        assert result is True

@pytest.mark.asyncio
async def test_is_blacklisted_token_false():
    """
    Test if a token is correctly identified as not blacklisted.
    """
    mock_db = AsyncMock()
    mock_db.token_blacklist.find_one.return_value = None

    with patch('services.auth_services.db', mock_db):
        auth_service = AuthService()
        token_to_check = "non_blacklisted_token"
        
        result = await auth_service.is_blacklisted_token(token_to_check)

        # Assertions
        mock_db.token_blacklist.find_one.assert_called_once_with({"token": token_to_check})
        assert result is False

