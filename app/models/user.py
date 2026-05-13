from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy.orm import relationship

from datetime import datetime

from app.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(100)
    )

    email = Column(
        String(100),
        unique=True
    )

    password = Column(
        String(255)
    )

    role = Column(
        String(50),
        default="reader"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    posts = relationship(
         "Post",
          back_populates="author"
)

    comments = relationship(
        "Comment",
         back_populates="user"
)