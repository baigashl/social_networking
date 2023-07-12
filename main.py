from fastapi import FastAPI
from api import auth, posts
from core.database import Base, engine

app = FastAPI()

# Include API routers
app.include_router(auth.router)
app.include_router(posts.router)


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Drop tables (for testing/demo purposes)
def drop_tables():
    Base.metadata.drop_all(bind=engine)


# Run migrations
def run_migrations():
    import subprocess

    subprocess.run(["alembic", "upgrade", "head"])


# Perform necessary setup actions
def setup():
    create_tables()
    run_migrations()


setup()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)










# from typing import List, Optional
# from fastapi import FastAPI, HTTPException, Depends
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from pydantic import BaseModel
# from jose import JWTError, jwt
# from passlib.context import CryptContext
# import requests
# from datetime import datetime, timedelta
# from sqlalchemy import create_engine, Column, Integer, String, Boolean
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
#
# # Define FastAPI app
# app = FastAPI()
#
# # JWT config
# SECRET_KEY = "your-secret-key"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30
#
# # PostgreSQL config
# DATABASE_URL = "postgresql://your-database-url"
#
# # Create SQLAlchemy engine and session
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#
# # ORM base model
# Base = declarative_base()
#
#
# # OAuth2 password bearer
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
#
# # Password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#
#
# # Models
# class User(Base):
#     __tablename__ = "users"
#
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True)
#     email = Column(String, unique=True, index=True)
#     password = Column(String)
#     full_name = Column(String)
#     disabled = Column(Boolean, default=False)
#
#
# class UserCreate(BaseModel):
#     username: str
#     email: str
#     password: str
#     full_name: Optional[str] = None
#
#
# class UserUpdate(BaseModel):
#     email: Optional[str] = None
#     password: Optional[str] = None
#     full_name: Optional[str] = None
#
#
# class Post(Base):
#     __tablename__ = "posts"
#
#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String)
#     content = Column(String)
#     author = Column(String)
#     likes = Column(Integer, default=0)
#     dislikes = Column(Integer, default=0)
#
#
# # Authentication
# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)
#
#
# def get_password_hash(password):
#     return pwd_context.hash(password)
#
#
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#
#
# def get_user(username: str, db):
#     return db.query(User).filter(User.username == username).first()
#
#
# def authenticate_user(username: str, password: str, db):
#     user = get_user(username, db)
#     if not user:
#         return None
#     if not verify_password(password, user.password):
#         return None
#     return user
#
#
# # Token generation
# def create_access_token(data: dict, expires_minutes: int):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt
#
#
# # Routes
# @app.post("/token")
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
#     user = authenticate_user(form_data.username, form_data.password, db)
#     if not user:
#         raise HTTPException(status_code=400, detail="Invalid username or password")
#     access_token = create_access_token(
#         data={"sub": user.username}, expires_minutes=ACCESS_TOKEN_EXPIRE_MINUTES
#     )
#     return {"access_token": access_token, "token_type": "bearer"}
#
#
# @app.post("/users/", response_model=User)
# def create_user(user: UserCreate, db=Depends(get_db)):
#     existing_user = User.get_user_by_username(user.username)
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Username already taken")
#
#     # Check if the email exists using emailhunter.co
#     email_verification_url = f"https://api.emailhunter.co/v2/email-verifier?email={user.email}&api_key=bc907f911ec2e970c32e6ba89dc76c82b9f00146"
#     response = requests.get(email_verification_url)
#     if response.status_code != 200 or not response.json().get("result") == "deliverable":
#         raise HTTPException(status_code=400, detail="Email does not exist")
#
#     # Use clearbit.com to get additional user data
#     clearbit_enrichment_url = f"https://person-stream.clearbit.com/v2/people/find?email={user.email}&api_key=pk_76bea57118c3cea2f1d4f418797dd138"
#     response = requests.get(clearbit_enrichment_url)
#     if response.status_code == 200:
#         user_data = response.json()
#         user.full_name = user_data.get("name", {}).get("fullName")
#
#     hashed_password = get_password_hash(user.password)
#     new_user = User(
#         username=user.username,
#         email=user.email,
#         password=hashed_password,
#         full_name=user.full_name,
#         disabled=False,
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user
#
#
# @app.get("/users/me", response_model=User)
# def read_user_me(current_user: User = Depends(get_user)):
#     return current_user
#
#
# @app.put("/users/me", response_model=User)
# def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_user), db=Depends(get_db)):
#     if user_update.email:
#         current_user.email = user_update.email
#     if user_update.password:
#         current_user.password = get_password_hash(user_update.password)
#     if user_update.full_name:
#         current_user.full_name = user_update.full_name
#     db.commit()
#     return current_user
#
#
# @app.get("/posts", response_model=List[Post])
# def get_posts(db=Depends(get_db)):
#     return db.query(Post).all()
#
#
# @app.post("/posts", response_model=Post)
# def create_post(post: Post, current_user: User = Depends(get_user), db=Depends(get_db)):
#     new_post = Post(
#         title=post.title,
#         content=post.content,
#         author=current_user.username,
#         likes=post.likes,
#         dislikes=post.dislikes,
#     )
#     db.add(new_post)
#     db.commit()
#     db.refresh(new_post)
#     return new_post
#
#
# @app.get("/posts/{post_id}", response_model=Post)
# def get_post(post_id: int, db=Depends(get_db)):
#     post = db.query(Post).filter(Post.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     return post
#
#
# @app.put("/posts/{post_id}", response_model=Post)
# def update_post(post_id: int, post_update: Post, current_user: User = Depends(get_user), db=Depends(get_db)):
#     post = db.query(Post).filter(Post.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     if post.author != current_user.username:
#         raise HTTPException(status_code=403, detail="Not authorized to update this post")
#     if post_update.title:
#         post.title = post_update.title
#     if post_update.content:
#         post.content = post_update.content
#     db.commit()
#     return post
#
#
# @app.delete("/posts/{post_id}")
# def delete_post(post_id: int, current_user: User = Depends(get_user),db=Depends(get_db)):
#     post = db.query(Post).filter(Post.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     if post.author != current_user.username:
#         raise HTTPException(status_code=403, detail="Not authorized to delete this post")
#     db.delete(post)
#     db.commit()
#     return {"message": "Post deleted"}
#
#
# @app.post("/posts/{post_id}/like")
# def like_post(post_id: int, current_user: User = Depends(get_user), db=Depends(get_db)):
#     post = db.query(Post).filter(Post.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     if post.author == current_user.username:
#         raise HTTPException(status_code=400, detail="Cannot like your own post")
#     post.likes += 1
#     db.commit()
#     return {"message": "Post liked"}
#
#
# @app.post("/posts/{post_id}/dislike")
# def dislike_post(post_id: int, current_user: User = Depends(get_user), db=Depends(get_db)):
#     post = db.query(Post).filter(Post.id == post_id).first()
#     if not post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     if post.author == current_user.username:
#         raise HTTPException(status_code=400, detail="Cannot dislike your own post")
#     post.dislikes += 1
#     db.commit()
#     return {"message": "Post disliked"}
#
#
# if __name__ == "__main__":
#     import uvicorn
#
#     uvicorn.run(app, host="0.0.0.0", port=8000)
