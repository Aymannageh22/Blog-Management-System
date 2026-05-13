from pydantic import BaseModel


class CommentCreate(BaseModel):

    content: str


class CommentUpdate(BaseModel):

    content: str


class ReplyResponse(BaseModel):

    id: int

    content: str

    user: str


class CommentResponse(BaseModel):

    id: int

    content: str

    user: str

    replies: list[ReplyResponse]