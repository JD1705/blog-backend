import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from fastapi import HTTPException, status
from bson import ObjectId

# Import classes and schemas from your application
from src.services.comment_service import CommentService
from src.models.comment import Comment
from src.models.post import Post
from src.models.user import User
from src.schemas.comment import CommentCreate, CommentUpdate


# --- Fixtures for Mocking MongoDB Collections ---
@pytest_asyncio.fixture
async def mock_comments_collection():
    """Mocks the comments MongoDB collection."""
    collection = AsyncMock()
    collection.name = "comments"  # Add name attribute for better debugging
    return collection


@pytest_asyncio.fixture
async def mock_posts_collection():
    """Mocks the posts MongoDB collection."""
    collection = AsyncMock()
    collection.name = "posts"  # Add name attribute for better debugging
    return collection


@pytest_asyncio.fixture
async def mock_users_collection():
    """Mocks the users MongoDB collection."""
    collection = AsyncMock()
    collection.name = "users"  # Add name attribute for better debugging
    return collection


@pytest_asyncio.fixture
async def comment_service_instance(
    mock_comments_collection, mock_posts_collection, mock_users_collection, mocker
):
    """Provides an instance of CommentService with mocked database collections."""
    # Patch the database connection to return our mock collections
    mock_db = MagicMock()
    mock_db.comments = mock_comments_collection
    mock_db.posts = mock_posts_collection
    mock_db.users = mock_users_collection
    mocker.patch("services.comment_service.db.database", new_callable=mock_db)
    return CommentService()


# --- Fixtures for Test Data ---


@pytest.fixture
def mock_user_data():
    """Returns sample user data."""
    return {
        "_id": str(ObjectId()),
        "username": "testuser",
        "email": "test@example.com",
        "role": "user",
        "hashed_password": "hashedpassword",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def admin_user_data():
    """Returns sample admin user data."""
    return {
        "_id": str(ObjectId()),
        "username": "adminuser",
        "email": "admin@example.com",
        "role": "admin",
        "hashed_password": "hashedpassword",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def mock_post_data(mock_user_data):
    """Returns sample post data."""
    return {
        "_id": ObjectId(),
        "title": "Test Post",
        "slug": "test-post",
        "content": "This is a test post.",
        "author_id": mock_user_data["_id"],
        "author_username": mock_user_data["username"],
        "status": "published",
        "comments_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def mock_comment_create_schema():
    """Returns a sample CommentCreate schema instance."""
    return CommentCreate(content="This is a test comment.")


@pytest.fixture
def mock_comment_update_schema():
    """Returns a sample CommentUpdate schema instance."""
    return CommentUpdate(content="This is an updated comment.")


@pytest.fixture
def mock_comment_data(mock_user_data, mock_post_data):
    """Returns sample comment data."""
    return {
        "_id": ObjectId(),
        "post_id": str(mock_post_data["_id"]),
        "author_id": mock_user_data["_id"],
        "author_username": mock_user_data["username"],
        "content": "This is an existing comment.",
        "parent_id": None,
        "replies_count": 0,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_edited": False,
        "edited_at": None,
    }


# --- Test Cases for create_post_comment ---
@pytest.mark.asyncio
class TestCreatePostComment:
    async def test_create_comment_success_no_parent(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
        mock_comment_create_schema,
    ):
        # Implement test logic here
        pass

    async def test_create_comment_success_with_parent(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
        mock_comment_create_schema,
    ):
        # Implement test logic here
        pass

    async def test_create_comment_fail_unauthorized(
        self, comment_service_instance, mock_comment_create_schema
    ):
        # Implement test logic here
        pass

    async def test_create_comment_fail_post_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_user_data,
        mock_comment_create_schema,
    ):
        # Implement test logic here
        pass

    async def test_create_comment_fail_post_not_published(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_user_data,
        mock_comment_create_schema,
    ):
        # Implement test logic here
        pass

    async def test_create_comment_fail_parent_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
        mock_comment_create_schema,
    ):
        # Implement test logic here
        pass


# --- Test Cases for get_comments ---
@pytest.mark.asyncio
class TestGetComments:
    async def test_get_comments_success(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
    ):
        # Implement test logic here
        pass

    async def test_get_comments_fail_post_not_found(
        self, comment_service_instance, mock_posts_collection
    ):
        # Implement test logic here
        pass

    async def test_get_comments_with_pagination(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
    ):
        # Implement test logic here
        pass

    async def test_get_comments_deleted_for_non_admin(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
    ):
        # Implement test logic here
        pass

    async def test_get_comments_full_for_admin(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        admin_user_data,
    ):
        # Implement test logic here
        pass


# --- Test Cases for update_comment ---
@pytest.mark.asyncio
class TestUpdateComment:
    async def test_update_comment_success_owner_within_time(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        mock_user_data,
        mock_comment_update_schema,
    ):
        # Implement test logic here
        pass

    async def test_update_comment_success_admin_any_time(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        admin_user_data,
        mock_comment_update_schema,
    ):
        # Implement test logic here
        pass

    async def test_update_comment_fail_post_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_user_data,
        mock_comment_data,
        mock_comment_update_schema,
    ):
        # Implement test logic here
        pass

    async def test_update_comment_fail_unauthorized(
        self, comment_service_instance, mock_comment_data, mock_comment_update_schema
    ):
        # Implement test logic here
        pass

    async def test_update_comment_fail_comment_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
        mock_comment_update_schema,
    ):
        # Implement test logic here
        pass

    async def test_update_comment_fail_comment_deleted(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        mock_user_data,
        mock_comment_update_schema,
    ):
        # Implement test logic here
        pass

    async def test_update_comment_fail_not_author_and_not_admin(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        mock_user_data,
        mock_comment_update_schema,
    ):
        # Implement test logic here
        pass

    async def test_update_comment_fail_time_expired_not_admin(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        mock_user_data,
        mock_comment_update_schema,
    ):
        # Implement test logic here
        pass


# --- Test Cases for delete_comment ---
@pytest.mark.asyncio
class TestDeleteComment:
    async def test_delete_comment_success_owner(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        mock_user_data,
    ):
        # Implement test logic here
        pass

    async def test_delete_comment_success_admin(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        admin_user_data,
    ):
        # Implement test logic here
        pass

    async def test_delete_comment_fail_post_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_user_data,
        mock_comment_data,
    ):
        # Implement test logic here
        pass

    async def test_delete_comment_fail_unauthorized(
        self, comment_service_instance, mock_comment_data
    ):
        # Implement test logic here
        pass

    async def test_delete_comment_fail_comment_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
        mock_comment_data,
    ):
        # Implement test logic here
        pass

    async def test_delete_comment_fail_comment_already_deleted(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        mock_user_data,
    ):
        # Implement test logic here
        pass

    async def test_delete_comment_fail_not_author_and_not_admin(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        mock_user_data,
    ):
        # Implement test logic here
        pass
