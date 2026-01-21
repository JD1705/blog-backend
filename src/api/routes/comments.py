from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from api.dependencies import get_current_user
from models.user import User
from services.comment_service import CommentService
from schemas.comment import (
    CommentCreate,
    CommentFilters,
    CommentUpdate,
    CommentResponse,
)

router = APIRouter(prefix="/posts/{slug}/comments")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: CommentCreate,
    slug: str,
    comment_service: CommentService = Depends(),
    current_user: Optional[dict] = Depends(get_current_user),
):
    response = await comment_service.create_post_comment(comment, current_user, slug)

    comment_response = CommentResponse(
        id=str(response.id),
        author_id=str(response.author_id),
        content=response.content,
        author_username=response.author_username,
        parent_id=str(response.parent_id),
        created_at=response.created_at,
        deleted_at=response.deleted_at,
        is_deleted=response.is_deleted,
        is_edited=response.is_edited,
        replies_count=response.replies_count,
        post_id=str(response.post_id),
        updated_at=response.updated_at,
        edited_at=response.edited_at,
    )
    return comment_response


@router.get("/")
async def get_comments_in_post(
    slug: str,
    comment_service: CommentService = Depends(),
    current_user: Optional[dict] = Depends(get_current_user),
    sort_by: str = "newest",
    limit: int = 100,
    offset: int = 0,
):
    response = await comment_service.get_comments(
        slug, sort_by, limit, offset, current_user
    )

    return response


@router.put("/{comment_id}")
async def update_comment(
    slug: str,
    comment_id: str,
    update_data: CommentUpdate,
    comment_service: CommentService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    response = await comment_service.update_comment(
        slug, comment_id, update_data, current_user
    )

    comment_response = CommentResponse(
        id=str(response.id),
        author_id=str(response.author_id),
        content=response.content,
        author_username=response.author_username,
        parent_id=str(response.parent_id),
        created_at=response.created_at,
        deleted_at=response.deleted_at,
        is_deleted=response.is_deleted,
        is_edited=response.is_edited,
        replies_count=response.replies_count,
        post_id=str(response.post_id),
        updated_at=response.updated_at,
        edited_at=response.edited_at,
    )
    return comment_response
