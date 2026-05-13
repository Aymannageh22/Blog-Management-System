from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import SessionLocal

from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User

from app.schemas.comment_schema import CommentCreate
from app.schemas.comment_schema import CommentUpdate
from app.schemas.comment_schema import CommentResponse
from app.utils.dependencies import get_current_user
from fastapi import status
import logging

logger = logging.getLogger(__name__)


router = APIRouter()


# Database dependency
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# Create comment
@router.post("/posts/{post_id}/comments")
def create_comment(

    post_id: int,

    comment: CommentCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    # Check if post exists
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()




    if not post:

        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )


    # Create comment
    new_comment = Comment(

        content=comment.content,

        user_id=current_user.id,

        post_id=post_id
    )

    db.add(new_comment)

    db.commit()

    logger.info(
    f"Comment created by user: {current_user.username}"
)

    db.refresh(new_comment)

    return {
        "message": "Comment added successfully"
    }


# Reply to comment
@router.post(
    "/comments/{comment_id}/reply",
    status_code=status.HTTP_201_CREATED
)
def reply_to_comment(

    comment_id: int,

    comment: CommentCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    # Check parent comment
    parent_comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()


    if not parent_comment:

        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )


    # Create reply
    reply = Comment(

        content=comment.content,

        user_id=current_user.id,

        post_id=parent_comment.post_id,

        parent_comment_id=parent_comment.id
    )

    db.add(reply)

    db.commit()

    logger.info(
    f"Reply added by user: {current_user.username}"
)

    db.refresh(reply)

    return {
        "message": "Reply added successfully"
    }

# Get comments for specific post
@router.get(
    "/posts/{post_id}/comments",
    response_model=list[CommentResponse]
)
def get_comments(

    post_id: int,

    db: Session = Depends(get_db)
):

    post = db.query(Post).filter(
        Post.id == post_id
    ).first()


    if not post:

        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    logger.info(
    f"Comments retrieved for post id: {post_id}"
)


    return [

        {
            "id": comment.id,

            "content": comment.content,

            "user": comment.user.username,

            "replies": [

                {
                    "id": reply.id,

                    "content": reply.content,

                    "user": reply.user.username
                }

                for reply in comment.replies
            ]
        }

        for comment in post.comments

        if comment.parent_comment_id is None
    ]


# Update comment
@router.put("/comments/{comment_id}")
def update_comment(

    comment_id: int,

    updated_comment: CommentUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()


    if not comment:

        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )


    # Only admin or comment owner
    if (
        current_user.role != "admin"
        and comment.user_id != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )


    comment.content = updated_comment.content

    db.commit()

    logger.info(
    f"Comment updated by user: {current_user.username}"
)

    db.refresh(comment)

    return {
        "message": "Comment updated successfully"
    }



# Delete comment
@router.delete("/comments/{comment_id}")
def delete_comment(

    comment_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()


    if not comment:

        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )


    # Only admin or comment owner
    if (
        current_user.role != "admin"
        and comment.user_id != current_user.id
    ):

        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )


    db.delete(comment)

    db.commit()

    logger.info(
    f"Comment deleted by user: {current_user.username}"
)

    return {
        "message": "Comment deleted successfully"
    }