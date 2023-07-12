# import requests
# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session
# from starlette import status
#
# from core.database import get_db
# from core.security import authenticate_user, create_access_token, get_password_hash, decode_access_token, \
#     verify_password
# from db.models import User
# from api.schemas import Token, UserCreate, UserSchema, UserLogin
#
# router = APIRouter()
#
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
#
#
# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
#     decoded_token = decode_access_token(token)
#     if decoded_token is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid authentication token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     username = decoded_token.get("sub")
#     if not username:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid authentication token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     user = db.query(User).filter(User.username == username).first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return user
#
# @router.post("/auth/token", tags=["auth"], response_model=Token)
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.username == form_data.username).first()
#     if not user or not verify_password(form_data.password, user.password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token = create_access_token({"sub": user.username})
#     return {"access_token": access_token, "token_type": "bearer"}
#
#
# @router.post("/auth/register", tags=["auth"], response_model=UserSchema)
# def register(user: UserCreate, db=Depends(get_db)):
#     # Check if the email exists using emailhunter.co
#     email_verification_url = f"https://api.emailhunter.co/v2/email-verifier?email={user.email}&api_key=bc907f911ec2e970c32e6ba89dc76c82b9f00146"
#     response = requests.get(email_verification_url)
#     print(response)
#     print(response.json()['data'].get("result"))
#     if response.status_code != 200 or not response.json()['data'].get("result") == "deliverable":
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
#         full_name=user.full_name
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from db.models import User
from core.database import get_db
from .schemas import UserRegistration, UserLogin, UserProfile
from core.security import verify_password, create_access_token, decode_access_token, get_password_hash

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    decoded_token = decode_access_token(token)
    print(decoded_token)
    if decoded_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decoded_token.get("sub")
    print(user_id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    print(user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/auth/register", response_model=UserProfile, tags=["auth"])
def register(user: UserRegistration, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = User(username=user.username, email=user.email, full_name=user.full_name)
    new_user.password = get_password_hash(user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/auth/login", tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    access_token = create_access_token(user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserRegistration, tags=["auth"])
def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = db.query(User).get(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

