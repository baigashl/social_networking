from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.models import Post, User
from core.database import get_db
from .schemas import PostCreate, PostUpdate, PostResponse, LikePost, DislikePost, LikedPostResponse
from .auth import get_current_user

router = APIRouter()


@router.post("/posts", response_model=PostResponse, tags=["posts"])
def create_post(post: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_post = Post(title=post.title, content=post.content, author_id=current_user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get("/posts/{post_id}", response_model=PostResponse, tags=["posts"])
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).get(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.put("/posts/{post_id}", response_model=PostResponse, tags=["posts"])
def update_post(post_id: int, post: PostUpdate, db: Session = Depends(get_db)):
    existing_post = db.query(Post).get(post_id)
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    existing_post.title = post.title
    existing_post.content = post.content
    db.commit()
    db.refresh(existing_post)
    return existing_post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["posts"])
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).get(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    db.delete(post)
    db.commit()


@router.post("/posts/{post_id}/like", tags=["posts"])
def like_post(post_id: int, like_data: LikePost, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    post = db.query(Post).get(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if current_user.id == post.author_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot like your own post")
    if current_user in post.liked_by:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post already liked")
    post.liked_by.append(current_user)
    db.commit()
    return HTTPException(status_code=status.HTTP_200_OK, detail="Post liked")


@router.post("/posts/{post_id}/dislike", tags=["posts"])
def dislike_post(post_id: int, dislike_data: DislikePost, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    post = db.query(Post).get(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if current_user.id == post.author_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot dislike your own post")
    if current_user not in post.liked_by:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post not liked")
    post.liked_by.remove(current_user)
    db.commit()
    return HTTPException(status_code=status.HTTP_200_OK, detail="Post disliked")


@router.get("/liked-posts", response_model=LikedPostResponse, tags=["posts"])
def liked_posts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    liked_posts = current_user.liked_posts
    return {"liked_posts": liked_posts}
