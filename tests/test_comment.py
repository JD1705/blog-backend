import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from fastapi import HTTPException
from bson import ObjectId

# Import classes and schemas from your application
from src.services.comment_service import CommentService
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
    mocker.patch("services.comment_service.db.database", new=mock_db)
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
        "post_id": mock_post_data["_id"],
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
        mock_posts_collection.find_one.return_value = mock_post_data

        response = await comment_service_instance.create_post_comment(
            mock_comment_create_schema, mock_user_data, "test-post"
        )

        assert response.content == mock_comment_create_schema.content
        assert response.parent_id is None
        assert response.post_id == mock_post_data["_id"]
        assert str(response.author_id) == mock_user_data["_id"]

        mock_posts_collection.find_one.assert_called_once_with({"slug": "test-post"})
        mock_posts_collection.update_one.assert_called_once_with(
            {"slug": "test-post"},
            {"$set": {"comments_count": mock_post_data["comments_count"] + 1}},
        )
        mock_comments_collection.insert_one.assert_called_once()
        mock_comments_collection.find_one.assert_not_called()

    async def test_create_comment_success_with_parent(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
    ):
        comment_schema_with_parent_id = CommentCreate(
            content="This is a test comment", parent_id=str(ObjectId())
        )
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_comments_collection.find_one.return_value = {
            "_id": comment_schema_with_parent_id.parent_id,
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
        response = await comment_service_instance.create_post_comment(
            comment_schema_with_parent_id, mock_user_data, "test-post"
        )

        assert response.content == comment_schema_with_parent_id.content
        assert str(response.parent_id) == comment_schema_with_parent_id.parent_id
        assert response.post_id == mock_post_data["_id"]
        assert str(response.author_id) == mock_user_data["_id"]

        mock_posts_collection.find_one.assert_called_once_with({"slug": "test-post"})
        mock_posts_collection.update_one.assert_called_once_with(
            {"slug": "test-post"},
            {"$set": {"comments_count": mock_post_data["comments_count"] + 1}},
        )
        mock_comments_collection.insert_one.assert_called_once()
        mock_comments_collection.find_one.assert_called_once_with(
            {"_id": ObjectId(comment_schema_with_parent_id.parent_id)}
        )

    async def test_create_comment_fail_unauthorized(
        self, comment_service_instance, mock_comment_create_schema
    ):
        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.create_post_comment(
                mock_comment_create_schema, user=None, slug="test-post"
            )

        assert excinfo.value.detail == "You dont have Permissions to comment"
        assert excinfo.value.status_code == 401

    async def test_create_comment_fail_post_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_user_data,
        mock_comment_create_schema,
    ):
        mock_posts_collection.find_one.return_value = None

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.create_post_comment(
                mock_comment_create_schema, mock_user_data, "not-existing-post"
            )

        assert excinfo.value.detail == "Post Not found"
        assert excinfo.value.status_code == 404

        mock_posts_collection.find_one.assert_called_once()
        mock_posts_collection.update_one.assert_not_called()

    async def test_create_comment_fail_post_not_published(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_user_data,
        mock_comment_create_schema,
    ):
        mock_posts_collection.find_one.return_value = {
            "_id": ObjectId(),
            "title": "Test Post",
            "slug": "test-post",
            "content": "This is a test post.",
            "author_id": mock_user_data["_id"],
            "author_username": mock_user_data["username"],
            "status": "draft",
            "comments_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.create_post_comment(
                mock_comment_create_schema, mock_user_data, "test-post"
            )

        assert excinfo.value.detail == "Post Not found"
        assert excinfo.value.status_code == 404

        mock_posts_collection.find_one.assert_called_once()
        mock_posts_collection.update_one.assert_not_called()

    async def test_create_comment_fail_parent_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
    ):
        comment_schema_with_parent_id = CommentCreate(
            content="This is a test comment", parent_id=str(ObjectId())
        )
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_comments_collection.find_one.return_value = None

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.create_post_comment(
                comment_schema_with_parent_id, mock_user_data, "test-post"
            )

        assert excinfo.value.detail == "This comment doesnt exists"
        assert excinfo.value.status_code == 400

        mock_posts_collection.find_one.assert_called_once()
        mock_posts_collection.update_one.assert_not_called()
        mock_comments_collection.find_one.assert_called_once()
        mock_comments_collection.insert_one.assert_not_called()
        mock_comments_collection.update_one.assert_not_called()


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
        mock_comment_data,
    ):
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_to_list_awaitable = AsyncMock(return_value=[mock_comment_data])
        mock_cursor_object = MagicMock()
        mock_cursor_object.sort.return_value = mock_cursor_object
        mock_cursor_object.skip.return_value = mock_cursor_object
        mock_cursor_object.limit.return_value = mock_cursor_object
        mock_cursor_object.to_list = mock_to_list_awaitable
        mock_comments_collection.find = MagicMock(return_value=mock_cursor_object)
        mock_comments_collection.count_documents = AsyncMock(return_value=1)

        comments, metadata = await comment_service_instance.get_comments(
            "test-post", "newest", 10, 0, mock_user_data
        )

        assert isinstance(comments, list)
        assert len(comments) == 1
        assert comments[0].post_id == mock_post_data["_id"]

        assert metadata["total"] == 1
        assert metadata["has_more"] is False

        mock_comments_collection.count_documents.assert_called_once_with(
            {"post_id": mock_post_data["_id"]}
        )
        mock_comments_collection.find.assert_called_once_with(
            {"post_id": mock_post_data["_id"]}
        )
        mock_cursor_object.skip.assert_called_once_with(0)
        mock_cursor_object.limit.assert_called_once_with(10)
        mock_to_list_awaitable.assert_called_once()

    async def test_get_comments_fail_post_not_found(
        self, comment_service_instance, mock_posts_collection
    ):
        mock_posts_collection.find_one.return_value = None

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.get_comments(
                "test-post", "newest", 10, 0, None
            )

        assert excinfo.value.detail == "Post Not found"
        assert excinfo.value.status_code == 404

    async def test_get_comments_with_pagination(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
        mock_comment_data,
    ):
        mock_posts_collection.find_one.return_value = mock_post_data

        # Create multiple mock comments for pagination
        mock_comment_data_2 = {
            **mock_comment_data,
            "_id": ObjectId(),
            "content": "Another comment",
            "created_at": datetime.now(timezone.utc),
        }
        mock_comment_data_3 = {
            **mock_comment_data,
            "_id": ObjectId(),
            "content": "Third comment",
            "created_at": datetime.now(timezone.utc),
        }
        all_comments = [mock_comment_data, mock_comment_data_2, mock_comment_data_3]

        mock_to_list_awaitable = AsyncMock(
            return_value=[mock_comment_data_2]
        )  # Only expect one comment for this page
        mock_cursor_object = MagicMock()
        mock_cursor_object.sort.return_value = mock_cursor_object
        mock_cursor_object.skip.return_value = mock_cursor_object
        mock_cursor_object.limit.return_value = mock_cursor_object
        mock_cursor_object.to_list = mock_to_list_awaitable
        mock_comments_collection.find = MagicMock(return_value=mock_cursor_object)
        mock_comments_collection.count_documents = AsyncMock(
            return_value=len(all_comments)
        )

        # Test with limit=1, skip=1 (second comment)
        comments, metadata = await comment_service_instance.get_comments(
            "test-post", "newest", 1, 1, mock_user_data
        )

        assert isinstance(comments, list)
        assert len(comments) == 1
        assert comments[0].content == mock_comment_data_2["content"]

        assert metadata["total"] == len(all_comments)
        assert metadata["has_more"] is True  # Since there's a third comment

        mock_comments_collection.count_documents.assert_called_once_with(
            {"post_id": mock_post_data["_id"]}
        )
        mock_comments_collection.find.assert_called_once_with(
            {"post_id": mock_post_data["_id"]}
        )
        mock_cursor_object.skip.assert_called_once_with(1)
        mock_cursor_object.limit.assert_called_once_with(1)
        mock_to_list_awaitable.assert_called_once()

    async def test_get_comments_deleted_for_non_admin(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
        mock_comment_data,
    ):
        mock_posts_collection.find_one.return_value = mock_post_data

        deleted_comment_data = {
            **mock_comment_data,
            "is_deleted": True,
            "_id": ObjectId(),
        }
        active_comment_data = {
            **mock_comment_data,
            "is_deleted": False,
            "_id": ObjectId(),
        }

        mock_to_list_awaitable = AsyncMock(
            return_value=[active_comment_data]
        )  # Only active comments should be returned
        mock_cursor_object = MagicMock()
        mock_cursor_object.sort.return_value = mock_cursor_object
        mock_cursor_object.skip.return_value = mock_cursor_object
        mock_cursor_object.limit.return_value = mock_cursor_object
        mock_cursor_object.to_list = mock_to_list_awaitable
        mock_comments_collection.find = MagicMock(return_value=mock_cursor_object)

        # When querying for non-admin, count should exclude deleted comments
        mock_comments_collection.count_documents = AsyncMock(return_value=1)

        comments, metadata = await comment_service_instance.get_comments(
            "test-post", "newest", 10, 0, mock_user_data
        )

        assert isinstance(comments, list)
        assert len(comments) == 1
        assert comments[0].is_deleted is False
        assert comments[0].content == active_comment_data["content"]

        assert metadata["total"] == 1
        assert metadata["has_more"] is False

        mock_comments_collection.count_documents.assert_called_once_with(
            {
                "post_id": mock_post_data["_id"],
            }
        )
        mock_comments_collection.find.assert_called_once_with(
            {
                "post_id": mock_post_data["_id"],
            }
        )
        mock_cursor_object.skip.assert_called_once_with(0)
        mock_cursor_object.limit.assert_called_once_with(10)
        mock_to_list_awaitable.assert_called_once()

    async def test_get_comments_full_for_admin(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        admin_user_data,
        mock_comment_data,
    ):
        mock_posts_collection.find_one.return_value = mock_post_data

        deleted_comment_data = {
            **mock_comment_data,
            "is_deleted": True,
            "_id": ObjectId(),
        }
        active_comment_data = {
            **mock_comment_data,
            "is_deleted": False,
            "_id": ObjectId(),
        }

        mock_to_list_awaitable = AsyncMock(
            return_value=[active_comment_data, deleted_comment_data]
        )  # Admin should see all comments
        mock_cursor_object = MagicMock()
        mock_cursor_object.sort.return_value = mock_cursor_object
        mock_cursor_object.skip.return_value = mock_cursor_object
        mock_cursor_object.limit.return_value = mock_cursor_object
        mock_cursor_object.to_list = mock_to_list_awaitable
        mock_comments_collection.find = MagicMock(return_value=mock_cursor_object)

        # When querying for admin, count should include all comments (deleted or not)
        mock_comments_collection.count_documents = AsyncMock(return_value=2)

        comments, metadata = await comment_service_instance.get_comments(
            "test-post", "newest", 10, 0, admin_user_data
        )

        assert isinstance(comments, list)
        assert len(comments) == 2
        # Verify that both active and deleted comments are returned
        assert any(c.is_deleted is False for c in comments)
        assert any(c.is_deleted is True for c in comments)

        assert metadata["total"] == 2
        assert metadata["has_more"] is False

        mock_comments_collection.count_documents.assert_called_once_with(
            {"post_id": mock_post_data["_id"]}
        )
        mock_comments_collection.find.assert_called_once_with(
            {"post_id": mock_post_data["_id"]}
        )
        mock_cursor_object.skip.assert_called_once_with(0)
        mock_cursor_object.limit.assert_called_once_with(10)
        mock_to_list_awaitable.assert_called_once()


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
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_comments_collection.find_one.side_effect = [
            mock_comment_data,
            {
                "_id": mock_post_data["_id"],
                "post_id": str(mock_post_data["_id"]),
                "author_id": mock_user_data["_id"],
                "author_username": mock_user_data["username"],
                "content": "This is an updated comment.",
                "parent_id": None,
                "replies_count": 0,
                "is_deleted": False,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_edited": False,
                "edited_at": None,
            },
        ]

        response = await comment_service_instance.update_comment(
            "test-post",
            str(mock_comment_data["_id"]),
            mock_comment_update_schema,
            mock_user_data,
        )

        assert response.content == mock_comment_update_schema.content
        assert response.id == mock_post_data["_id"]
        assert response.post_id == mock_post_data["_id"]

        mock_comments_collection.find_one.assert_called()
        mock_posts_collection.find_one.assert_called_once()
        mock_comments_collection.update_one.assert_called_once()

    async def test_update_comment_fail_post_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_user_data,
        mock_comment_data,
        mock_comment_update_schema,
    ):
        mock_posts_collection.find_one.return_value = None

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.update_comment(
                "not-existing-post",
                str(mock_comment_data["_id"]),
                mock_comment_update_schema,
                mock_user_data,
            )

        assert excinfo.value.detail == "Post Not found"
        assert excinfo.value.status_code == 404

        mock_posts_collection.find_one.assert_called_once_with(
            {"slug": "not-existing-post"}
        )

    async def test_update_comment_fail_unauthorized(
        self,
        mock_posts_collection,
        mock_post_data,
        comment_service_instance,
        mock_comment_data,
        mock_comment_update_schema,
    ):
        mock_posts_collection.find_one.return_value = mock_post_data

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.update_comment(
                "test-post",
                str(mock_comment_data["_id"]),
                mock_comment_update_schema,
                None,
            )

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "You are Not Authenticated"

    async def test_update_comment_fail_comment_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
        mock_comment_data,
        mock_comment_update_schema,
    ):
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_comments_collection.find_one.return_value = None

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.update_comment(
                "test-post",
                str(mock_comment_data["_id"]),
                mock_comment_update_schema,
                mock_user_data,
            )

        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "Comment Not found"

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
        deleted_comment_data = {
            **mock_comment_data,
            "is_deleted": True,
            "_id": ObjectId(),
        }
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_comments_collection.find_one.return_value = deleted_comment_data

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.update_comment(
                "test-post",
                str(mock_comment_data["_id"]),
                mock_comment_update_schema,
                mock_user_data,
            )

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "This comment is deleted"

    async def test_update_comment_fail_not_author_and_not_admin(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        mock_comment_update_schema,
    ):
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_comments_collection.find_one.return_value = mock_comment_data

        not_author_data = {
            "_id": str(ObjectId()),
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "hashed_password": "hashedpassword",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.update_comment(
                "test-post",
                str(mock_comment_data["_id"]),
                mock_comment_update_schema,
                not_author_data,
            )

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail.lower() == "you dont have permission to do this"


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
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_comments_collection.find_one.return_value = mock_comment_data

        await comment_service_instance.delete_comment(
            "test-post", str(mock_comment_data["_id"]), mock_user_data
        )

        mock_posts_collection.find_one.assert_called_once_with({"slug": "test-post"})
        mock_comments_collection.find_one.assert_called_once_with(
            {"_id": mock_comment_data["_id"]}
        )
        mock_comments_collection.update_one.assert_called_once()
        call_args, _ = mock_comments_collection.update_one.call_args
        assert call_args[0] == {"_id": mock_comment_data["_id"]}

        update_set_payload = call_args[1]["$set"]
        assert update_set_payload["is_deleted"] is True
        assert "deleted_at" in update_set_payload

    async def test_delete_comment_fail_post_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_user_data,
        mock_comment_data,
    ):
        mock_posts_collection.find_one.return_value = None

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.delete_comment(
                "not-existing-post",
                str(mock_comment_data["_id"]),
                mock_user_data,
            )

        assert excinfo.value.detail == "Post Not found"
        assert excinfo.value.status_code == 404

        mock_posts_collection.find_one.assert_called_once_with(
            {"slug": "not-existing-post"}
        )

    async def test_delete_comment_fail_unauthorized(
        self, mock_posts_collection, comment_service_instance, mock_comment_data
    ):
        mock_posts_collection.find_one.return_value = mock_post_data

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.delete_comment(
                "test-post",
                str(mock_comment_data["_id"]),
                None,
            )

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "You are Not Authenticated"

        mock_posts_collection.find_one.assert_called_once()

    async def test_delete_comment_fail_comment_not_found(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_user_data,
        mock_comment_data,
    ):
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_comments_collection.find_one.return_value = None

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.delete_comment(
                "test-post",
                str(mock_comment_data["_id"]),
                mock_user_data,
            )

        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "Comment Not found"

        mock_posts_collection.find_one.assert_called_once()
        mock_comments_collection.find_one.assert_called_once()
        mock_comments_collection.update_one.assert_not_called()

    async def test_delete_comment_fail_comment_already_deleted(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        mock_user_data,
    ):
        deleted_comment_data = {
            **mock_comment_data,
            "is_deleted": True,
            "_id": ObjectId(),
        }
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_comments_collection.find_one.return_value = deleted_comment_data

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.delete_comment(
                "test-post",
                str(mock_comment_data["_id"]),
                mock_user_data,
            )

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "This comment is deleted"

        mock_posts_collection.find_one.assert_called_once()
        mock_comments_collection.find_one.assert_called_once()
        mock_comments_collection.update_one.assert_not_called()

    async def test_delete_comment_fail_not_author_and_not_admin(
        self,
        comment_service_instance,
        mock_posts_collection,
        mock_comments_collection,
        mock_post_data,
        mock_comment_data,
        mock_user_data,
    ):
        mock_posts_collection.find_one.return_value = mock_post_data
        mock_comments_collection.find_one.return_value = mock_comment_data

        not_author_data = {
            "_id": str(ObjectId()),
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "hashed_password": "hashedpassword",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        with pytest.raises(HTTPException) as excinfo:
            await comment_service_instance.delete_comment(
                "test-post",
                str(mock_comment_data["_id"]),
                not_author_data,
            )

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail.lower() == "you dont have permission to do this"

        mock_posts_collection.find_one.assert_called_once()
        mock_comments_collection.find_one.assert_called_once()
        mock_comments_collection.update_one.assert_not_called()
