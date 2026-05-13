from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import SessionLocal

from app.models.post import Post
from app.models.user import User
from functools import lru_cache

from app.schemas.post_schema import PostCreate
from app.schemas.post_schema import PostUpdate
from app.schemas.post_schema import PostResponse

from app.utils.dependencies import get_current_user
from app.models.comment import Comment
from fastapi import status
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=100)
def cached_posts_message():

    return "Posts cache active"


@lru_cache(maxsize=100)
def cached_single_post_message():

    return "Single post cache active"


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

    posts = db.query(Post).offset(skip).limit(limit).all()
   
    print(cached_posts_message())


  
    logger.info(
        f"Posts retrieved - page {page} with limit {limit}"
    )

    return [
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


# Get single post
@router.get(
    "/posts/{post_id}",
    response_model=PostResponse
)
def get_post(

    post_id: int,

    db: Session = Depends(get_db)
):

    post = db.query(Post).filter(
        Post.id == post_id
    ).first()

    print(cached_single_post_message())


    if not post:

        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    logger.info(
        f"Post retrieved with id: {post_id}"
    )


    return {

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