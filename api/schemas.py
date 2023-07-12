from pydantic import BaseModel
from typing import List
from db.models import User, Post


class Token(BaseModel):
    access_token: str
    token_type: str


class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    full_name: str

    class Config:
        from_attributes = True


class UserRegistration(BaseModel):
    username: str
    email: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    username: str
    password: str


class PostBase(BaseModel):
    title: str
    content: str


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    pass


class PostResponse(PostBase):
    id: int
    author: UserProfile

    class Config:
        from_attributes = True


class PostWithAuthorResponse(PostResponse):
    author: UserProfile


class LikePost(BaseModel):
    post_id: int


class DislikePost(BaseModel):
    post_id: int


class LikedPostResponse(BaseModel):
    liked_posts: List[PostResponse]