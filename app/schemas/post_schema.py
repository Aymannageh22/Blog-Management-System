from pydantic import BaseModel
from app.schemas.comment_schema import CommentResponse
from datetime import datetime
from typing import Optional

class PostCreate(BaseModel):

    title: str

    content: str


class PostUpdate(BaseModel):

    title: str

    content: str


class PostResponse(BaseModel):

    id: int

    title: str

    content: str

    author: str

    created_at: Optional[datetime] = None

    comments: list[CommentResponse]