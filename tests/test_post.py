import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from services.post_service import PostService
from models.user import User
from models.post import Post
from schemas.post import PostCreate, PostUpdate, PostFilters
from fastapi import HTTPException, status


# Fixture for a mock User (author)
@pytest.fixture
def mock_author_user():
    return User(
        id=str("60a7b1c3d4e5f6g7h8i9j0k1"),
        username="authoruser",
        email="author@example.com",
        hashed_password="hashedpassword",
        bio="Author bio",
        role="author",
        is_active=True,
        posts_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

# Fixture for a mock Admin User
@pytest.fixture
def mock_admin_user():
    return User(
        id=str(ObjectId()),
        username="adminuser",
        email="admin@example.com",
        hashed_password="hashedpassword",
        bio="Admin bio",
        role="admin",
        is_active=True,
        posts_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

# Fixture for a mock User (regular user)
@pytest.fixture
def mock_regular_user():
    return User(
        id=str(ObjectId()),
        username="regularuser",
        email="regular@example.com",
        hashed_password="hashedpassword",
        bio="Regular user bio",
        role="reader",
        is_active=True,
        posts_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# Fixture for a mock PostCreate object
@pytest.fixture
def mock_post_create():
    return PostCreate(
        title="Test Post Title",
        content="This is the content of the test post.",
        tags=["test", "python"],
        featured_image="http://example.com/image.jpg",
    )

# Fixture for a mock PostUpdate object
@pytest.fixture
def mock_post_update():
    return PostUpdate(
        title="Updated Post Title",
        content="This is the updated content.",
        tags=["updated", "python", "fastapi"],
    )

# Fixture for a mock PostFilters object
@pytest.fixture
def mock_post_filters():
    return PostFilters(status="published", author_username="authoruser")

# Fixture for a mock Post object
@pytest.fixture
def mock_post(mock_author_user):
    return Post(
        id=str(ObjectId()),
        title="Existing Post",
        content="Content of existing post.",
        slug="existing-post",
        author_username=mock_author_user.username,
        author_id=str(mock_author_user.id),
        tags=["existing"],
        featured_image="http://example.com/existing.jpg",
        status="published",
        view_count=10,
        comments_count=2,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        published_at=datetime.now(timezone.utc),
    )

@pytest.fixture
def mock_post_json(mock_author_user):
    return {
        "_id":str(ObjectId()),
        "title":"Existing Post",
        "content":"Content of existing post.",
        "slug":"existing-post",
        "author_username":"authoruser",
        "author_id":mock_author_user.id,
        "tags":["existing"],
        "featured_image":"http://example.com/existing.jpg",
        "status":"draft",
        "view_count":10,
        "comments_count":2,
        "created_at":datetime.now(timezone.utc),
        "updated_at":datetime.now(timezone.utc),
        "published_at":None,

    }

@pytest.fixture
def mock_many_posts_json(mock_author_user):
    posts = []
    for i in range(25):
        post_data = {
            "_id": str(ObjectId()),
            "title": f"Post Title {i}",
            "content": f"Content of post {i}.",
            "slug": f"post-title-{i}",
            "author_username": mock_author_user.username,
            "author_id": mock_author_user.id,
            "tags": ["test", f"tag-{i % 3}"],
            "featured_image": "http://example.com/image.jpg",
            "status": "published",
            "view_count": i,
            "comments_count": i % 5,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "published_at": datetime.now(timezone.utc),
        }
        posts.append(post_data)
    return posts


################################################################################
# create_post tests
################################################################################
@patch("services.post_service.verify_unique_slug", new_callable=AsyncMock)
@patch("services.post_service.db.database",  new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_create_post_success(mock_db, mock_verify_slug, mock_post_create, mock_author_user):
    """
    Test case for successful creation of a post by an authorized user.
    """
    mock_verify_slug.return_value = "test-post-title"
    mock_db.users.update_one.return_value = AsyncMock()
    mock_db.posts.insert_one.return_value = AsyncMock()
    
    post_service = PostService()
    response = await post_service.create_post(mock_post_create, mock_author_user)

    assert isinstance(response, Post)
    assert response.slug == "test-post-title"
    assert response.author_username == mock_author_user.username
    assert response.author_id == mock_author_user.id

    mock_db.users.update_one.assert_called_once()
    call_args, _ = mock_db.users.update_one.call_args
    assert call_args[0] == {"_id": mock_author_user.id}

    # Check the $set operator content
    update_set_payload = call_args[1]["$set"]
    assert update_set_payload["posts_count"] == mock_author_user.posts_count
    assert "updated_at" in update_set_payload # Check that updated_at was added

    mock_db.posts.insert_one.assert_called_once()


@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_create_post_unauthorized(mock_db, mock_post_create, mock_regular_user):
    """
    Test case for creating a post by an unauthorized user.
    """
    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        response = await post_service.create_post(mock_post_create, mock_regular_user)

    assert excinfo.value.detail == "Not Enought Permissions"
    assert excinfo.value.status_code == 401

    mock_db.users.update_one.assert_not_called()
    mock_db.posts.insert_one.assert_not_called()

################################################################################
# get_post_by_slug tests
################################################################################
@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_post_by_slug_success_published(mock_db, mock_post):
    """
    Test case for successfully retrieving a published post by slug.
    """
    mock_db.posts.find_one.return_value = mock_post.to_mongo_dict()
    mock_db.posts.update_one.return_value = AsyncMock()

    post_service = PostService()

    response = await post_service.get_post_by_slug("existing-post")

    assert isinstance(response, Post)
    assert response.slug == "existing-post"
    assert response.author_username == "authoruser"

    mock_db.posts.update_one.assert_called_once()
    call_args, _ = mock_db.posts.update_one.call_args
    assert call_args[0] == {"slug": "existing-post"}

    # Check the $set operator content
    update_set_payload = call_args[1]["$inc"]
    assert update_set_payload["view_count"] == 1

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_post_by_slug_not_found(mock_db):
    """
    Test case for retrieving a non-existent post.
    """
    mock_db.posts.find_one.return_value = None
    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.get_post_by_slug("not-existing-post")

    assert excinfo.value.detail == "Post Not Found"
    assert excinfo.value.status_code == 404

    mock_db.posts.update_one.assert_not_called()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_post_by_slug_draft_unauthorized(mock_db, mock_regular_user):
    """
    Test case for retrieving a draft post by an unauthorized user.
    """
    mock_db.posts.find_one.return_value = {
        "_id":str(ObjectId()),
        "title":"Existing Post",
        "content":"Content of existing post.",
        "slug":"existing-post",
        "author_username":"authoruser",
        "author_id":str("60a7b1c3d4e5f6g7h8i9j0k1"),
        "tags":["existing"],
        "featured_image":"http://example.com/existing.jpg",
        "status":"draft",
        "view_count":10,
        "comments_count":2,
        "created_at":datetime.now(timezone.utc),
        "updated_at":datetime.now(timezone.utc),
        "published_at":None,

    }
    
    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.get_post_by_slug("existing-post", mock_regular_user.model_dump())

    assert excinfo.value.detail == "Post Not Found"
    assert excinfo.value.status_code == 404

    mock_db.posts.update_one.assert_not_called()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_post_by_slug_draft_authorized(mock_db, mock_author_user):
    """
    Test case for retrieving a draft post by an authorized user (author or admin).
    """
    mock_db.posts.find_one.return_value = {
        "_id":str(ObjectId()),
        "title":"Existing Post",
        "content":"Content of existing post.",
        "slug":"existing-post",
        "author_username":"authoruser",
        "author_id":mock_author_user.id,
        "tags":["existing"],
        "featured_image":"http://example.com/existing.jpg",
        "status":"draft",
        "view_count":10,
        "comments_count":2,
        "created_at":datetime.now(timezone.utc),
        "updated_at":datetime.now(timezone.utc),
        "published_at":None,

    }
    post_service = PostService()

    response = await post_service.get_post_by_slug("existing-post", mock_author_user.model_dump())

    assert isinstance(response, Post)
    assert response.slug == "existing-post"
    assert response.author_username == "authoruser"

    mock_db.posts.update_one.assert_not_called()


################################################################################
# update_post tests
################################################################################
@patch("services.post_service.verify_unique_slug", new_callable=AsyncMock)
@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_update_post_success_by_author(mock_db, mock_verify_slug, mock_post_json, mock_post_update, mock_author_user):
    """
    Test case for successful update of a post by its author.
    """
    mock_db.posts.find_one.side_effect = [mock_post_json, {
        "_id":str(ObjectId()),
        "title":"Updated Post Title",
        "content":"This is the updated content.",
        "slug":"updated-post-title",
        "author_username":"authoruser",
        "author_id":mock_author_user.id,
        "tags":["existing", "updated", "python", "fastapi"],
        "featured_image":"http://example.com/existing.jpg",
        "status":"draft",
        "view_count":10,
        "comments_count":2,
        "created_at":datetime.now(timezone.utc),
        "updated_at":datetime.now(timezone.utc),
        "published_at":None,

    }
]
    mock_db.posts.update_one.return_value = AsyncMock()

    mock_verify_slug.return_value = "updated-post-title"

    post_service = PostService()

    response = await post_service.update_post("existing-post", mock_post_update, mock_author_user)
    
    assert isinstance(response, Post)
    assert response.title == mock_post_update.title
    assert response.content == mock_post_update.content
    assert response.slug == "updated-post-title"
    for i in mock_post_update.tags:
        assert i in response.tags

    mock_db.posts.find_one.assert_called()
    mock_db.posts.update_one.assert_called_once()


@patch("services.post_service.verify_unique_slug", new_callable=AsyncMock)
@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_update_post_success_by_admin(mock_db, mock_verify_slug, mock_post_json, mock_post_update, mock_admin_user):
    """
    Test case for successful update of a post by an admin.
    """
    mock_db.posts.find_one.side_effect = [mock_post_json, {
        "_id":str(ObjectId()),
        "title":"Updated Post Title",
        "content":"This is the updated content.",
        "slug":"updated-post-title",
        "author_username":"authoruser",
        "author_id":mock_post_json["author_id"],
        "tags":["existing", "updated", "python", "fastapi"],
        "featured_image":"http://example.com/existing.jpg",
        "status":"draft",
        "view_count":10,
        "comments_count":2,
        "created_at":datetime.now(timezone.utc),
        "updated_at":datetime.now(timezone.utc),
        "published_at":None,

    }
]
    mock_db.posts.update_one.return_value = AsyncMock()

    mock_verify_slug.return_value = "updated-post-title"

    post_service = PostService()

    response = await post_service.update_post("existing-post", mock_post_update, mock_admin_user)
    
    assert isinstance(response, Post)
    assert response.title == mock_post_update.title
    assert response.content == mock_post_update.content
    assert response.slug == "updated-post-title"
    for i in mock_post_update.tags:
        assert i in response.tags

    mock_db.posts.find_one.assert_called()
    mock_db.posts.update_one.assert_called_once()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_update_post_not_found(mock_db, mock_post_update, mock_author_user):
    """
    Test case for updating a non-existent post.
    """
    mock_db.posts.find_one.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.update_post("not-existing-post", mock_post_update, mock_author_user)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Post Not Found"

    mock_db.posts.find_one.assert_called_once()
    mock_db.posts.update_one.assert_not_called()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_update_post_unauthorized_other_author(mock_db, mock_post_json, mock_post_update, mock_regular_user):
    """
    Test case for unauthorized update of a post by another regular user.
    """
    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.update_post("existing-post", mock_post_update, mock_regular_user)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "You dont have Permissions"

    mock_db.posts.find_one.assert_not_called()
    mock_db.posts.update_one.assert_not_called()


################################################################################
# delete_post tests
################################################################################
@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_delete_post_success_by_author(mock_db, mock_post_json, mock_author_user):
    """
    Test case for successful deletion of a post by its author.
    """
    mock_db.posts.find_one.return_value = mock_post_json
    mock_db.users.update_one.return_value = AsyncMock()
    mock_db.posts.delete_one.return_value.deleted_count = 1
    
    post_service = PostService()

    response = await post_service.delete_post("existing-post", mock_author_user)

    assert response is True
    
    mock_db.users.update_one.assert_called_once()
    call_args, _ = mock_db.users.update_one.call_args
    assert call_args[0] == {"username": mock_post_json["author_username"]}

    update_set_payload = call_args[1]["$set"]
    assert update_set_payload["posts_count"] == -1
    assert "updated_at" in update_set_payload 

    mock_db.posts.find_one.assert_called_once_with({"slug":"existing-post"})
    mock_db.posts.delete_one.assert_called_once_with({"slug":"existing-post"})

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_delete_post_success_by_admin(mock_db, mock_post_json, mock_admin_user):
    """
    Test case for successful deletion of a post by an admin.
    """
    mock_db.posts.find_one.return_value = mock_post_json
    mock_db.users.update_one.return_value = AsyncMock()
    mock_db.posts.delete_one.return_value.deleted_count = 1
    
    post_service = PostService()

    response = await post_service.delete_post("existing-post", mock_admin_user)

    assert response is True
    
    mock_db.users.update_one.assert_called_once()
    call_args, _ = mock_db.users.update_one.call_args
    assert call_args[0] == {"username": mock_post_json["author_username"]}

    update_set_payload = call_args[1]["$set"]
    assert update_set_payload["posts_count"] == -1
    assert "updated_at" in update_set_payload 

    mock_db.posts.find_one.assert_called_once_with({"slug":"existing-post"})
    mock_db.posts.delete_one.assert_called_once_with({"slug":"existing-post"})

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_delete_post_not_found(mock_db, mock_author_user):
    """
    Test case for deleting a non-existent post.
    """
    mock_db.posts.find_one.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.delete_post("not-existing-post", mock_author_user)

    assert excinfo.value.detail == "Post Not Found"
    assert excinfo.value.status_code == 404

    mock_db.posts.delete_one.assert_not_called()
    mock_db.users.update_one.assert_not_called()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_delete_post_unauthorized_other_author(mock_db, mock_post_json, mock_regular_user):
    """
    Test case for unauthorized deletion of a post by another user.
    """
    mock_db.posts.find_one.return_value = mock_post_json

    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.delete_post("existing-post", mock_regular_user)

    assert excinfo.value.detail == "You dont have Permissions"
    assert excinfo.value.status_code == 401

    mock_db.posts.find_one.assert_called_once_with({"slug":"existing-post"})
    mock_db.posts.delete_one.assert_not_called()
    mock_db.users.update_one.assert_not_called()

################################################################################
# publish_post tests
################################################################################
@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_publish_post_success(mock_db, mock_post_json, mock_author_user):
    """
    Test case for successfully publishing a draft post.
    """
    mock_db.posts.find_one.side_effect = [mock_post_json, {
        "_id":str(ObjectId()),
        "title":"Existing Post",
        "content":"Content of existing post.",
        "slug":"existing-post",
        "author_username":"authoruser",
        "author_id":mock_author_user.id,
        "tags":["existing"],
        "featured_image":"http://example.com/existing.jpg",
        "status":"published",
        "view_count":10,
        "comments_count":2,
        "created_at":datetime.now(timezone.utc),
        "updated_at":datetime.now(timezone.utc),
        "published_at":datetime.now(timezone.utc)
    }
]
    mock_db.posts.update_one.return_value = AsyncMock()
    
    post_service = PostService()
    response = await post_service.publish_post("existing-post", mock_author_user)

    assert response.status == "published"
    mock_db.posts.update_one.assert_called_once()
    call_args, _ = mock_db.posts.update_one.call_args
    assert call_args[0] == {"slug": "existing-post"}

    update_set_payload = call_args[1]["$set"]
    assert update_set_payload["status"] == "published"
    assert "updated_at" in update_set_payload
    assert "published_at" in update_set_payload

    mock_db.posts.find_one.assert_called()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_publish_post_already_published(mock_db, mock_author_user):
    """
    Test case for attempting to publish an already published post.
    """
    mock_db.posts.find_one.return_value = {
        "_id":str(ObjectId()),
        "title":"Existing Post",
        "content":"Content of existing post.",
        "slug":"existing-post",
        "author_username":"authoruser",
        "author_id":mock_author_user.id,
        "tags":["existing"],
        "featured_image":"http://example.com/existing.jpg",
        "status":"published",
        "view_count":10,
        "comments_count":2,
        "created_at":datetime.now(timezone.utc),
        "updated_at":datetime.now(timezone.utc),
        "published_at":datetime.now(timezone.utc)
    }
    
    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.publish_post("existing-post", mock_author_user)

    assert excinfo.value.detail == "Post Already published"
    assert excinfo.value.status_code == 409

    mock_db.posts.find_one.assert_called_once()
    mock_db.posts.update_one.assert_not_called()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_publish_post_not_found(mock_db, mock_author_user):
    """
    Test case for publishing a non-existent post.
    """
    mock_db.posts.find_one.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.publish_post("not-existing-post", mock_author_user)

    assert excinfo.value.detail == "Post Not Found"
    assert excinfo.value.status_code == 404

    mock_db.posts.update_one.assert_not_called()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_publish_post_unauthorized(mock_db, mock_post_json, mock_regular_user):
    """
    Test case for unauthorized publishing of a post by a regular user.
    """
    mock_db.posts.find_one.return_value = mock_post_json

    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.publish_post("existing-post", mock_regular_user)

    assert excinfo.value.detail == "You dont have Permissions"
    assert excinfo.value.status_code == 401

    mock_db.posts.find_one.assert_called_once_with({"slug":"existing-post"})
    mock_db.posts.update_one.assert_not_called()

################################################################################
# archive_post tests
################################################################################
@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_archive_post_success(mock_db, mock_post_json, mock_author_user):
    """
    Test case for successfully archiving a published post.
    """
    mock_db.posts.find_one.side_effect = [mock_post_json, {
        "_id":str(ObjectId()),
        "title":"Existing Post",
        "content":"Content of existing post.",
        "slug":"existing-post",
        "author_username":"authoruser",
        "author_id":mock_author_user.id,
        "tags":["existing"],
        "featured_image":"http://example.com/existing.jpg",
        "status":"archived",
        "view_count":10,
        "comments_count":2,
        "created_at":datetime.now(timezone.utc),
        "updated_at":datetime.now(timezone.utc),
        "published_at":None
    }
]
    mock_db.posts.update_one.return_value = AsyncMock()
    
    post_service = PostService()
    response = await post_service.archive_post("existing-post", mock_author_user)

    assert response.status == "archived"
    mock_db.posts.update_one.assert_called_once()
    call_args, _ = mock_db.posts.update_one.call_args
    assert call_args[0] == {"slug": "existing-post"}

    update_set_payload = call_args[1]["$set"]
    assert update_set_payload["status"] == "archived"
    assert "updated_at" in update_set_payload

    mock_db.posts.find_one.assert_called()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_archive_post_already_archived(mock_db, mock_post_json, mock_author_user):
    """
    Test case for attempting to archive an already archived post.
    """
    mock_db.posts.find_one.return_value = {
        "_id":str(ObjectId()),
        "title":"Existing Post",
        "content":"Content of existing post.",
        "slug":"existing-post",
        "author_username":"authoruser",
        "author_id":mock_author_user.id,
        "tags":["existing"],
        "featured_image":"http://example.com/existing.jpg",
        "status":"archived",
        "view_count":10,
        "comments_count":2,
        "created_at":datetime.now(timezone.utc),
        "updated_at":datetime.now(timezone.utc),
        "published_at":None
    }
    
    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.archive_post("existing-post", mock_author_user)

    assert excinfo.value.detail == "Post Already archived"
    assert excinfo.value.status_code == 409

    mock_db.posts.find_one.assert_called_once()
    mock_db.posts.update_one.assert_not_called()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_archive_post_not_found(mock_db, mock_author_user):
    """
    Test case for archiving a non-existent post.
    """
    mock_db.posts.find_one.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.archive_post("not-existing-post", mock_author_user)

    assert excinfo.value.detail == "Post Not Found"
    assert excinfo.value.status_code == 404

    mock_db.posts.update_one.assert_not_called()

@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_archive_post_unauthorized(mock_db, mock_post_json, mock_regular_user):
    """
    Test case for unauthorized archiving of a post by a regular user.
    """
    mock_db.posts.find_one.return_value = mock_post_json

    with pytest.raises(HTTPException) as excinfo:
        post_service = PostService()

        await post_service.archive_post("existing-post", mock_regular_user)

    assert excinfo.value.detail == "You dont have Permissions"
    assert excinfo.value.status_code == 401

    mock_db.posts.find_one.assert_called_once_with({"slug":"existing-post"})
    mock_db.posts.update_one.assert_not_called()


################################################################################
# list_posts tests
################################################################################
@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_list_posts_no_filters(mock_db, mock_post_json, mock_regular_user):
    """
    Test case for listing all published posts without any filters.
    """
    mock_db.posts.count_documents.return_value = 1

    mock_find_result = MagicMock()
    mock_find_result.sort.return_value = mock_find_result
    mock_find_result.skip.return_value = mock_find_result
    mock_find_result.limit.return_value = mock_find_result

    mock_find_result.to_list = AsyncMock(return_value=[mock_post_json])

    mock_db.posts.find = MagicMock(return_value=mock_find_result)

    post_filters = PostFilters()
    post_service = PostService()

    posts, metadata = await post_service.list_posts(post_filters, mock_regular_user)

    assert isinstance(posts, list)
    assert len(posts) == 1
    assert isinstance(posts[0], Post)
    assert posts[0].slug == mock_post_json["slug"]

    assert metadata["page"] == 1
    assert metadata["per_page"] == 10
    assert metadata["total"] == 1 # docs_count
    assert metadata["total_pages"] == 1
    assert metadata["has_next"] is False
    assert metadata["has_prev"] is False

    mock_db.posts.count_documents.assert_called_once_with({"status": "published"})
    mock_db.posts.find.assert_called_once_with({"status": "published"})

    mock_find_result.sort.assert_called_once_with("published_at", -1)
    mock_find_result.skip.assert_called_once_with(0)
    mock_find_result.limit.assert_called_once_with(10)
    mock_find_result.to_list.assert_called_once()


@patch("services.post_service.db.database", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_list_posts_with_status_filter(mock_posts_collection, mock_regular_user, mock_post_json):
    """
    Test case for listing posts with a status filter.
    """
    # Create a published version of the mock post
    published_post_json = mock_post_json.copy()
    published_post_json["status"] = "published"
    published_post_json["published_at"] = datetime.now(timezone.utc)

    # Mock count_documents
    mock_posts_collection.posts.count_documents = AsyncMock(return_value=1)
    
    # Configure the mock for chained calls
    mock_to_list_awaitable = AsyncMock(return_value=[published_post_json])
    mock_cursor_object = MagicMock()
    mock_cursor_object.sort.return_value = mock_cursor_object
    mock_cursor_object.skip.return_value = mock_cursor_object
    mock_cursor_object.limit.return_value = mock_cursor_object
    mock_cursor_object.to_list = mock_to_list_awaitable
    mock_posts_collection.posts.find = MagicMock(return_value=mock_cursor_object)

    post_filters = PostFilters(status="published")
    post_service = PostService()

    posts, metadata = await post_service.list_posts(post_filters, mock_regular_user)

    assert isinstance(posts, list)
    assert len(posts) == 1
    assert isinstance(posts[0], Post)
    assert posts[0].slug == published_post_json["slug"]
    assert posts[0].status == "published"

    assert metadata["total"] == 1
    assert metadata["total_pages"] == 1

    mock_posts_collection.posts.count_documents.assert_called_once_with({"status": "published"})
    mock_posts_collection.posts.find.assert_called_once_with({"status": "published"})
    mock_cursor_object.sort.assert_called_once_with("published_at", -1)
    mock_cursor_object.skip.assert_called_once_with(0)
    mock_cursor_object.limit.assert_called_once_with(10)
    mock_to_list_awaitable.assert_called_once()


@patch("services.post_service.db.database")
@pytest.mark.asyncio
async def test_list_posts_with_author_filter(mock_posts_collection, mock_regular_user, mock_post_json):
    """
    Test case for listing posts with an author filter.
    """
    # mock_post_json already has author_username="authoruser"
    
    # Mock count_documents
    mock_posts_collection.posts.count_documents = AsyncMock(return_value=1)
    
    # Configure the mock for chained calls
    mock_to_list_awaitable = AsyncMock(return_value=[mock_post_json])
    mock_cursor_object = MagicMock()
    mock_cursor_object.sort.return_value = mock_cursor_object
    mock_cursor_object.skip.return_value = mock_cursor_object
    mock_cursor_object.limit.return_value = mock_cursor_object
    mock_cursor_object.to_list = mock_to_list_awaitable
    mock_posts_collection.posts.find = MagicMock(return_value=mock_cursor_object)

    author_username_filter = "authoruser"
    post_filters = PostFilters(author_username=author_username_filter)
    post_service = PostService()

    posts, metadata = await post_service.list_posts(post_filters, mock_regular_user)

    assert isinstance(posts, list)
    assert len(posts) == 1
    assert isinstance(posts[0], Post)
    assert posts[0].author_username == author_username_filter

    assert metadata["total"] == 1
    assert metadata["total_pages"] == 1

    # Verify calls
    mock_posts_collection.posts.count_documents.assert_called_once_with({
        "status": "published", # The code always adds status="published" for list_posts
        "author_username": author_username_filter
    })
    mock_posts_collection.posts.find.assert_called_once_with({
        "status": "published",
        "author_username": author_username_filter
    })
    mock_cursor_object.sort.assert_called_once_with("published_at", -1)
    mock_cursor_object.skip.assert_called_once_with(0)
    mock_cursor_object.limit.assert_called_once_with(10)
    mock_to_list_awaitable.assert_called_once()


@patch("services.post_service.db.database")
@pytest.mark.asyncio
async def test_list_posts_with_tags_filter(mock_posts_collection, mock_regular_user, mock_post_json):
    """
    Test case for listing posts with a tags filter.
    """
    # mock_post_json already has tags=["existing"]
    
    # Mock count_documents
    mock_posts_collection.posts.count_documents = AsyncMock(return_value=1)
    
    # Configure the mock for chained calls
    mock_to_list_awaitable = AsyncMock(return_value=[mock_post_json])
    mock_cursor_object = MagicMock()
    mock_cursor_object.sort.return_value = mock_cursor_object
    mock_cursor_object.skip.return_value = mock_cursor_object
    mock_cursor_object.limit.return_value = mock_cursor_object
    mock_cursor_object.to_list = mock_to_list_awaitable
    mock_posts_collection.posts.find = MagicMock(return_value=mock_cursor_object)

    tags_filter = ["existing"]
    post_filters = PostFilters(tags=tags_filter)
    post_service = PostService()

    posts, metadata = await post_service.list_posts(post_filters, mock_regular_user)

    assert isinstance(posts, list)
    assert len(posts) == 1
    assert isinstance(posts[0], Post)
    # Check if all tags in the filter are present in the post's tags
    assert all(tag in posts[0].tags for tag in tags_filter)

    assert metadata["total"] == 1
    assert metadata["total_pages"] == 1

    # Verify calls
    mock_posts_collection.posts.count_documents.assert_called_once_with({
        "status": "published",
        "tags": {"$all": tags_filter}
    })
    mock_posts_collection.posts.find.assert_called_once_with({
        "status": "published",
        "tags": {"$all": tags_filter}
    })
    mock_cursor_object.sort.assert_called_once_with("published_at", -1)
    mock_cursor_object.skip.assert_called_once_with(0)
    mock_cursor_object.limit.assert_called_once_with(10)
    mock_to_list_awaitable.assert_called_once()


@patch("services.post_service.db.database")
@pytest.mark.asyncio
async def test_list_posts_with_search_filter(mock_posts_collection, mock_regular_user, mock_post_json):
    """
    Test case for listing posts with a search filter.
    """
    # mock_post_json title: "Existing Post", content: "Content of existing post."
    
    # Mock count_documents
    mock_posts_collection.posts.count_documents = AsyncMock(return_value=1)
    
    # Configure the mock for chained calls
    mock_to_list_awaitable = AsyncMock(return_value=[mock_post_json])
    mock_cursor_object = MagicMock()
    mock_cursor_object.sort.return_value = mock_cursor_object
    mock_cursor_object.skip.return_value = mock_cursor_object
    mock_cursor_object.limit.return_value = mock_cursor_object
    mock_cursor_object.to_list = mock_to_list_awaitable
    mock_posts_collection.posts.find = MagicMock(return_value=mock_cursor_object)

    search_query = "existing"
    post_filters = PostFilters(search=search_query)
    post_service = PostService()

    posts, metadata = await post_service.list_posts(post_filters, mock_regular_user)

    assert isinstance(posts, list)
    assert len(posts) == 1
    assert isinstance(posts[0], Post)
    assert search_query in posts[0].title.lower() or search_query in posts[0].content.lower()

    assert metadata["total"] == 1
    assert metadata["total_pages"] == 1

    # Verify calls
    mock_posts_collection.posts.count_documents.assert_called_once_with({
        "status": "published",
        "$text": {"$search": search_query}
    })
    mock_posts_collection.posts.find.assert_called_once_with({
        "status": "published",
        "$text": {"$search": search_query}
    })
    mock_cursor_object.sort.assert_called_once_with("published_at", -1)
    mock_cursor_object.skip.assert_called_once_with(0)
    mock_cursor_object.limit.assert_called_once_with(10)
    mock_to_list_awaitable.assert_called_once()


@patch("services.post_service.db.database")
@pytest.mark.asyncio
async def test_list_posts_pagination(mock_posts_collection, mock_regular_user, mock_many_posts_json):
    """
    Test case for listing posts with pagination.
    """
    total_posts = len(mock_many_posts_json)
    page = 2
    per_page = 10
    skip = (page - 1) * per_page # Expected skip: 10
    expected_posts_for_page = mock_many_posts_json[skip : skip + per_page] # Posts 10-19

    mock_posts_collection.posts.count_documents = AsyncMock(return_value=total_posts)
    
    mock_to_list_awaitable = AsyncMock(return_value=expected_posts_for_page)
    mock_cursor_object = MagicMock()
    mock_cursor_object.sort.return_value = mock_cursor_object
    mock_cursor_object.skip.return_value = mock_cursor_object
    mock_cursor_object.limit.return_value = mock_cursor_object
    mock_cursor_object.to_list = mock_to_list_awaitable
    mock_posts_collection.posts.find = MagicMock(return_value=mock_cursor_object)

    post_filters = PostFilters()
    post_service = PostService()

    posts, metadata = await post_service.list_posts(post_filters, mock_regular_user, page=page, per_page=per_page)

    assert isinstance(posts, list)
    assert len(posts) == per_page
    assert posts[0].slug == Post.from_mongo_dict(expected_posts_for_page[0]).slug
    assert posts[-1].slug == Post.from_mongo_dict(expected_posts_for_page[-1]).slug

    assert metadata["page"] == page
    assert metadata["per_page"] == per_page
    assert metadata["total"] == total_posts
    assert metadata["total_pages"] == (total_posts + per_page - 1) // per_page # (25 + 10 - 1) // 10 = 3
    assert metadata["has_next"] is True # page 2 of 3
    assert metadata["has_prev"] is True # page 2 of 3

    mock_posts_collection.posts.count_documents.assert_called_once_with({"status": "published"})
    mock_posts_collection.posts.find.assert_called_once_with({"status": "published"})
    mock_cursor_object.sort.assert_called_once_with("published_at", -1)
    mock_cursor_object.skip.assert_called_once_with(skip)
    mock_cursor_object.limit.assert_called_once_with(per_page)
    mock_to_list_awaitable.assert_called_once()



################################################################################
# list_self_posts tests
################################################################################
@patch("services.post_service.db.database")
@pytest.mark.asyncio
async def test_list_self_posts_success(mock_posts_collection, mock_author_user, mock_post_json):
    """
    Test case for successfully listing posts created by the current user.
    """
    # mock_post_json already has author_username="authoruser" matching mock_author_user
    
    # Mock count_documents
    mock_posts_collection.posts.count_documents = AsyncMock(return_value=1)
    
    # Configure the mock for chained calls
    mock_to_list_awaitable = AsyncMock(return_value=[mock_post_json])
    mock_cursor_object = MagicMock()
    mock_cursor_object.sort.return_value = mock_cursor_object
    mock_cursor_object.skip.return_value = mock_cursor_object
    mock_cursor_object.limit.return_value = mock_cursor_object
    mock_cursor_object.to_list = mock_to_list_awaitable
    mock_posts_collection.posts.find = MagicMock(return_value=mock_cursor_object)

    post_filters = PostFilters()
    post_service = PostService()

    posts, metadata = await post_service.list_self_posts(post_filters, mock_author_user)

    assert isinstance(posts, list)
    assert len(posts) == 1
    assert isinstance(posts[0], Post)
    assert posts[0].author_username == mock_author_user.username

    assert metadata["total"] == 1
    assert metadata["total_pages"] == 1

    # Verify calls
    mock_posts_collection.posts.count_documents.assert_called_once_with({
        "author_username": mock_author_user.username
    })
    mock_posts_collection.posts.find.assert_called_once_with({
        "author_username": mock_author_user.username
    })
    mock_cursor_object.sort.assert_called_once_with("published_at", -1)
    mock_cursor_object.skip.assert_called_once_with(0)
    mock_cursor_object.limit.assert_called_once_with(10)
    mock_to_list_awaitable.assert_called_once()


@patch("services.post_service.db.database")
@pytest.mark.asyncio
async def test_list_self_posts_with_filters(mock_posts_collection, mock_author_user, mock_post_json):
    """
    Test case for listing posts by current user with filters.
    """
    # mock_post_json already has author_username="authoruser" and tags=["existing"]
    
    # Mock count_documents
    mock_posts_collection.posts.count_documents = AsyncMock(return_value=1)
    
    # Configure the mock for chained calls
    mock_to_list_awaitable = AsyncMock(return_value=[mock_post_json])
    mock_cursor_object = MagicMock()
    mock_cursor_object.sort.return_value = mock_cursor_object
    mock_cursor_object.skip.return_value = mock_cursor_object
    mock_cursor_object.limit.return_value = mock_cursor_object
    mock_cursor_object.to_list = mock_to_list_awaitable
    mock_posts_collection.posts.find = MagicMock(return_value=mock_cursor_object)

    tags_filter = ["existing"]
    post_filters = PostFilters(tags=tags_filter)
    post_service = PostService()

    posts, metadata = await post_service.list_self_posts(post_filters, mock_author_user)

    assert isinstance(posts, list)
    assert len(posts) == 1
    assert isinstance(posts[0], Post)
    assert posts[0].author_username == mock_author_user.username
    assert all(tag in posts[0].tags for tag in tags_filter)

    assert metadata["total"] == 1
    assert metadata["total_pages"] == 1

    # Verify calls
    expected_query = {
        "author_username": mock_author_user.username,
        "tags": {"$all": tags_filter}
    }
    mock_posts_collection.posts.count_documents.assert_called_once_with(expected_query)
    mock_posts_collection.posts.find.assert_called_once_with(expected_query)
    mock_cursor_object.sort.assert_called_once_with("published_at", -1)
    mock_cursor_object.skip.assert_called_once_with(0)
    mock_cursor_object.limit.assert_called_once_with(10)
    mock_to_list_awaitable.assert_called_once()


@patch("services.post_service.db.database")
@pytest.mark.asyncio
async def test_list_self_posts_no_posts(mock_posts_collection, mock_author_user):
    """
    Test case for listing posts by current user when no posts exist.
    """
    # Mock count_documents to return 0
    mock_posts_collection.posts.count_documents = AsyncMock(return_value=0)
    
    # Configure the mock for chained calls to return an empty list
    mock_to_list_awaitable = AsyncMock(return_value=[])
    mock_cursor_object = MagicMock()
    mock_cursor_object.sort.return_value = mock_cursor_object
    mock_cursor_object.skip.return_value = mock_cursor_object
    mock_cursor_object.limit.return_value = mock_cursor_object
    mock_cursor_object.to_list = mock_to_list_awaitable
    mock_posts_collection.posts.find = MagicMock(return_value=mock_cursor_object)

    post_filters = PostFilters()
    post_service = PostService()

    posts, metadata = await post_service.list_self_posts(post_filters, mock_author_user)

    assert isinstance(posts, list)
    assert len(posts) == 0

    assert metadata["page"] == 1
    assert metadata["per_page"] == 10
    assert metadata["total"] == 0
    assert metadata["total_pages"] == 0
    assert metadata["has_next"] is False
    assert metadata["has_prev"] is False

    # Verify calls
    expected_query = {
        "author_username": mock_author_user.username
    }
    mock_posts_collection.posts.count_documents.assert_called_once_with(expected_query)
    mock_posts_collection.posts.find.assert_called_once_with(expected_query)
    mock_cursor_object.sort.assert_called_once_with("published_at", -1)
    mock_cursor_object.skip.assert_called_once_with(0)
    mock_cursor_object.limit.assert_called_once_with(10)
    mock_to_list_awaitable.assert_called_once()

