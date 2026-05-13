from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime

from datetime import datetime

from app.database import Base
from sqlalchemy.orm import relationship


class Comment(Base):

    __tablename__ = "comments"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    content = Column(
        Text
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    post_id = Column(
        Integer,
        ForeignKey("posts.id")
    )

    parent_comment_id = Column(
        Integer,
        ForeignKey("comments.id"),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship(
        "User",
        back_populates="comments"
    )

    post = relationship(
        "Post",
        back_populates="comments"
    )

    replies = relationship(
        "Comment"
    )