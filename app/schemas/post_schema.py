from pydantic import BaseModel
from app.schemas.comment_schema import CommentResponse

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

    comments: list[CommentResponse]