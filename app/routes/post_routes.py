from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import SessionLocal

from app.models.post import Post
from app.models.user import User

from app.schemas.post_schema import PostCreate
from app.schemas.post_schema import PostUpdate
from app.schemas.post_schema import PostResponse

from app.utils.dependencies import get_current_user
from app.models.comment import Comment
from fastapi import status
import logging

logger = logging.getLogger(__name__)

import json

from app.redis_client import redis_client

router = APIRouter()


# Database dependency
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# Create Post
@router.post(
    "/posts",
    status_code=status.HTTP_201_CREATED
)
def create_post(

    post: PostCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    # Allow only author and admin
    if current_user.role not in ["author", "admin"]:

        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )


    new_post = Post(

        title=post.title,
        content=post.content,
        author_id=current_user.id
    )

    # Save to database
    db.add(new_post)

    db.commit()
    redis_client.flushdb()

    logger.info(
        f"Post created by user: {current_user.username}"
    )

    db.refresh(new_post)

    return {
        "message": "Post created successfully"
    }


# Get all posts with pagination
@router.get(
    "/posts",
    response_model=list[PostResponse]
)
def get_posts(

    page: int = 1,

    limit: int = 5,

    db: Session = Depends(get_db)
):

    skip = (page - 1) * limit

    cache_key = f"posts_page_{page}_limit_{limit}"

    cached_posts = redis_client.get(cache_key)

    if cached_posts:

        logger.info(
            "Posts retrieved from Redis cache"
        )

        return json.loads(cached_posts)

    posts = db.query(Post).offset(skip).limit(limit).all()

    posts_data = [
        {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "author": post.author.username,
            "comments": [

                build_comment_tree(comment)

                for comment in post.comments

                if comment.parent_comment_id is None
            ]
        }

        for post in posts
    ]


    redis_client.set(

        cache_key,

        json.dumps(posts_data),

        ex=60
    )


    logger.info(
        f"Posts retrieved - page {page} with limit {limit}"
    )

    return posts_data


# Get single post
@router.get(
    "/posts/{post_id}",
    response_model=PostResponse
)
def get_post(

    post_id: int,

    db: Session = Depends(get_db)
):

    cache_key = f"post_{post_id}"

    cached_post = redis_client.get(cache_key)

    if cached_post:

        logger.info(
            f"Post {post_id} retrieved from Redis cache"
        )

        return json.loads(cached_post)

    post = db.query(Post).filter(
        Post.id == post_id
    ).first()


    if not post:

        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    logger.info(
        f"Post retrieved with id: {post_id}"
    )

    post_data = {

        "id": post.id,

        "title": post.title,

        "content": post.content,

        "author": post.author.username,

        "comments": [

            build_comment_tree(comment)

            for comment in post.comments

            if comment.parent_comment_id is None
        ]
    }

    redis_client.set(

        cache_key,

        json.dumps(post_data),

        ex=60
    )

    return post_data

# Update post
@router.put("/posts/{post_id}")
def update_post(

    post_id: int,

    updated_post: PostUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    post = db.query(Post).filter(
        Post.id == post_id
    ).first()


    if not post:

        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )


    # Only admin or post owner
    if (
        current_user.role != "admin"
        and post.author_id != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )


    post.title = updated_post.title
    post.content = updated_post.content


    db.commit()

    redis_client.flushdb()

    logger.info(
        f"Post updated by user: {current_user.username}"
    )

    db.refresh(post)

    return {
        "message": "Post updated successfully"
    }


# Delete post
@router.delete("/posts/{post_id}")
def delete_post(

    post_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    post = db.query(Post).filter(
        Post.id == post_id
    ).first()


    if not post:

        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )


    # Only admin or owner can delete
    if (
        current_user.role != "admin"
        and post.author_id != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )


    db.delete(post)

    db.commit()
    redis_client.flushdb()

    logger.info(
        f"Post deleted by user: {current_user.username}"
    )

    return {
        "message": "Post deleted successfully"
    }


# Build nested replies
def build_comment_tree(comment):

    return {

        "id": comment.id,

        "content": comment.content,

        "user": comment.user.username,

        "replies": [

            build_comment_tree(reply)

            for reply in comment.replies
        ]
    }