import pytest
from unittest.mock import AsyncMock, call, patch

from services.user_service import UserService
from schemas.user import UserResponse, UserUpdate
from fastapi import HTTPException, status
from datetime import datetime, timezone

# Assuming that db.database will be mocked at a higher level,
# or injected, as it's a direct import.
# We'll mock the 'db.database' calls directly within tests for now.


# Fixture for UserService instance
@pytest.fixture
def user_service():
    return UserService()


# Fixture for a mock current_user
@pytest.fixture
def mock_current_user():
    return {
        "_id": "60a7b1c3d4e5f6g7h8i9j0k1",
        "username": "testuser",
        "email": "test@example.com",
        "bio": "Test bio",
        "role": "user",
        "posts_count": 5,
        "created_at": datetime.now(timezone.utc),
    }


# Fixture for a mock UserUpdate object
@pytest.fixture
def mock_user_update():
    return UserUpdate(username="newusername", bio="New bio")


################################################################################
# get_user_profile tests
################################################################################
@pytest.mark.asyncio
async def test_get_user_profile_success(user_service, mock_current_user):
    """
    Test case for successful retrieval of user profile.
    """
    response = await user_service.get_user_profile(mock_current_user)

    assert isinstance(response, UserResponse)
    assert response.id == mock_current_user["_id"]
    assert response.username == mock_current_user["username"]
    assert response.bio == mock_current_user["bio"]
    assert response.email == mock_current_user["email"]


################################################################################
# update_user_profile tests
################################################################################
@pytest.mark.asyncio
async def test_update_user_profile_success_no_email_change(
    user_service, mock_current_user, mock_user_update
):
    """
    Test case for successful update of user profile without changing email.
    """
@pytest.mark.asyncio
async def test_update_user_profile_success_no_email_change(
    mock_current_user, mock_user_update
):
    """
    Test case for successful update of user profile without changing email.
    """
    
    mock_db = AsyncMock()
    mock_db.users.update_one.return_value = AsyncMock() # Simulate UpdateResult
    
    # Mock the find_one call that happens AFTER the update
    # The `updated_at` field will be set by the service, so we need to account for it.
    expected_updated_user_in_db = {
            "username": mock_user_update.username,
            "bio": mock_user_update.bio,
            "_id": mock_current_user["_id"],
            "role": mock_current_user["role"],
            "email": mock_current_user["email"],
            "posts_count": mock_current_user["posts_count"],
            "created_at": mock_current_user["created_at"],
            "updated_at": datetime.now(timezone.utc) # Placeholder for assertion
            }
    mock_db.users.find_one.return_value = expected_updated_user_in_db
    
    with patch("services.user_service.db", mock_db):
        user_service = UserService() # Instantiate UserService AFTER patching db
        response = await user_service.update_user_profile(mock_current_user, mock_user_update)

        # Assertions
        assert isinstance(response, UserResponse)
        assert response.username == mock_user_update.username
        assert response.bio == mock_user_update.bio
        assert response.email == mock_current_user["email"]
        assert response.id == str(mock_current_user["_id"])

        # Verify update_one was called correctly
        mock_db.users.update_one.assert_called_once()
        call_args, _ = mock_db.users.update_one.call_args
        assert call_args[0] == {"_id": mock_current_user["_id"]}
        
        # Check the $set operator content
        update_set_payload = call_args[1]["$set"]
        assert update_set_payload["username"] == mock_user_update.username
        assert update_set_payload["bio"] == mock_user_update.bio
        assert "updated_at" in update_set_payload # Check that updated_at was added

        # Verify find_one was called after update to retrieve the updated user
        mock_db.users.find_one.assert_called_once_with({"_id": mock_current_user["_id"]})


@pytest.mark.asyncio
@patch("services.user_service.db", new_callable=AsyncMock)
async def test_update_user_profile_success_with_new_email(
    mock_db, mock_current_user
):
    """
    Test case for successful update of user profile with a new email that doesn't exist.
    """
    mock_update_data = UserUpdate(username="newusername",email="newemail@test.com")
    mock_db.users.update_one.return_value = AsyncMock()

    expected_updated_user_in_db = {
            "username": mock_update_data.username,
            "bio": mock_current_user["bio"],
            "_id": mock_current_user["_id"],
            "role": mock_current_user["role"],
            "email": mock_update_data.email,
            "posts_count": mock_current_user["posts_count"],
            "created_at": mock_current_user["created_at"],
            "updated_at": datetime.now(timezone.utc) # Placeholder for assertion
            }

    mock_db.users.find_one.side_effect = [None, expected_updated_user_in_db]

    user_service = UserService()
    response = await user_service.update_user_profile(mock_current_user, mock_update_data)

    assert isinstance(response, UserResponse)
    assert response.username == mock_update_data.username
    assert response.bio == mock_current_user["bio"]
    assert response.email == mock_update_data.email
    assert response.id == str(mock_current_user["_id"])

    # Verify update_one was called correctly
    mock_db.users.update_one.assert_called_once()
    call_args, _ = mock_db.users.update_one.call_args
    assert call_args[0] == {"_id": mock_current_user["_id"]}

    # Check the $set operator content
    update_set_payload = call_args[1]["$set"]
    assert update_set_payload["username"] == mock_update_data.username
    assert update_set_payload["email"] == mock_update_data.email
    assert "updated_at" in update_set_payload # Check that updated_at was added

    # check the find_one calls
    assert mock_db.users.find_one.call_count == 2
    assert mock_db.users.find_one.call_args_list[0] == call({"email":mock_update_data.email})
    assert mock_db.users.find_one.call_args_list[1] == call({"_id":mock_current_user["_id"]})

@pytest.mark.asyncio
@patch("services.user_service.db", new_callable=AsyncMock)
async def test_update_user_profile_email_already_exists(
    mock_db, mock_current_user
):
    """
    Test case for when update fails because the new email already exists for another user.
    """
    mock_update_data = UserUpdate(username="newusername",email="newemail@test.com")
    user_already_in_db = {
            "username": mock_update_data.username,
            "bio": mock_current_user["bio"],
            "_id": mock_current_user["_id"],
            "role": mock_current_user["role"],
            "email": mock_update_data.email,
            "posts_count": mock_current_user["posts_count"],
            "created_at": mock_current_user["created_at"],
            "updated_at": datetime.now(timezone.utc) # Placeholder for assertion
            }

    mock_db.users.find_one.return_value = user_already_in_db
    
    user_service = UserService()
    with pytest.raises(HTTPException) as excinfo:
        await user_service.update_user_profile(mock_current_user, mock_update_data)

    assert excinfo.value.status_code == status.HTTP_409_CONFLICT
    assert excinfo.value.detail == "Incorrect Credentials"
    mock_db.users.find_one.assert_called_once_with({"email":mock_update_data.email})
    mock_db.users.update_one.assert_not_called()


@pytest.mark.asyncio
@patch("services.user_service.db", new_callable=AsyncMock)
async def test_update_user_profile_partial_update(
    mock_db, mock_current_user
):
    """
    Test case for updating only a subset of fields (e.g., only bio).
    """
    mock_update_data = UserUpdate(username="newusername")
    mock_db.users.update_one.return_value = AsyncMock()

    expected_updated_user_in_db = {
            "username": mock_update_data.username,
            "bio": mock_current_user["bio"],
            "_id": mock_current_user["_id"],
            "role": mock_current_user["role"],
            "email": mock_current_user["email"],
            "posts_count": mock_current_user["posts_count"],
            "created_at": mock_current_user["created_at"],
            "updated_at": datetime.now(timezone.utc) # Placeholder for assertion
            }

    mock_db.users.find_one.return_value = expected_updated_user_in_db
    user_service = UserService()
    response = await user_service.update_user_profile(mock_current_user, mock_update_data)

    assert isinstance(response, UserResponse)
    assert response.username == mock_update_data.username
    assert response.bio == mock_current_user["bio"]
    assert response.email == mock_current_user["email"]
    assert response.id == str(mock_current_user["_id"])

    # Verify update_one was called correctly
    mock_db.users.update_one.assert_called_once()
    call_args, _ = mock_db.users.update_one.call_args
    assert call_args[0] == {"_id": mock_current_user["_id"]}

    # Check the $set operator content
    update_set_payload = call_args[1]["$set"]
    assert update_set_payload["username"] == mock_update_data.username
    assert "updated_at" in update_set_payload # Check that updated_at was added

    # Verify find_one was called after update to retrieve the updated user
    mock_db.users.find_one.assert_called_once_with({"_id": mock_current_user["_id"]})


################################################################################
# deactivate_user tests
################################################################################
@pytest.mark.asyncio
@patch("src.core.database.db.database")
async def test_deactivate_user_success(mock_db, user_service, mock_current_user):
    """
    Test case for successful deactivation of a user.
    """
    pass
