from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import get_current_user
from models.user import User
from services.post_service import PostService
from schemas.post import PostCreate, PostFilters, PostUpdate, PostResponse

router = APIRouter(prefix="/posts")


@router.post("/")
async def create_posts(
    post_data: PostCreate,
    post_service: PostService = Depends(),
    author: dict = Depends(get_current_user),
):
    response = await post_service.create_post(
        post_data, author=User.from_mongo_dict(author)
    )

    return PostResponse(
        title=response.title,
        content=response.content,
        author_id=str(response.author_id),
        tags=response.tags,
        featured_image=response.featured_image,
        id=str(response.id),
        slug=response.slug,
        author_username=response.author_username,
        status=response.status,
        view_count=response.view_count,
        comments_count=response.comments_count,
        created_at=response.created_at,
        updated_at=response.updated_at,
        published_at=response.published_at,
    )


@router.get("/{slug}")
async def get_post_by_slug(
    slug: str,
    post_service: PostService = Depends(),
    current_user: Optional[dict] = Depends(get_current_user),
):
    response = await post_service.get_post_by_slug(slug, current_user)

    return PostResponse(
        title=response.title,
        content=response.content,
        author_id=str(response.author_id),
        tags=response.tags,
        featured_image=response.featured_image,
        id=str(response.id),
        slug=response.slug,
        author_username=response.author_username,
        status=response.status,
        view_count=response.view_count,
        comments_count=response.comments_count,
        created_at=response.created_at,
        updated_at=response.updated_at,
        published_at=response.published_at,
    )


@router.put("/{slug}")
async def update_post_by_slug(
    slug: str,
    update_data: PostUpdate,
    post_service: PostService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    response = await post_service.update_post(
        slug, update_data, user=User.from_mongo_dict(current_user)
    )

    return PostResponse(
        title=response.title,
        content=response.content,
        author_id=str(response.author_id),
        tags=response.tags,
        featured_image=response.featured_image,
        id=str(response.id),
        slug=response.slug,
        author_username=response.author_username,
        status=response.status,
        view_count=response.view_count,
        comments_count=response.comments_count,
        created_at=response.created_at,
        updated_at=response.updated_at,
        published_at=response.published_at,
    )
