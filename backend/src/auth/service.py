from fastapi import HTTPException
from sqlalchemy.orm import Session
from entities import UserProfile as User
from .models import UserCreate, UserLogin
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import re


load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")


# Utils

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # Encode to bytes and truncate to 72 bytes max
    password_bytes = password.encode("utf-8")[:72]
    return pwd_context.hash(password_bytes.decode("utf-8", errors="ignore"))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(
        timezone.utc) + (expires_delta or timedelta(minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES)))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Register User
def register_user(user: UserCreate, db: Session):

    if len(user.username) < 6:
        raise HTTPException(
            status_code=400, detail="Username must be at least 6 characters")

    if not re.match(r".+\.[a-zA-Z]{2,3}$", user.email):
        raise HTTPException(
            status_code=400, detail="Email must have a valid domain (e.g. example.com)")

    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        hashed = hash_password(user.password)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Password too long. Max 72 characters allowed.")

    new_user = User(username=user.username, email=user.email,
                    hashed_password=hashed, postal_code=user.postal_code, created_at=datetime.now(timezone.utc))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# Authenticate User
def authenticate_user(user: UserLogin, db: Session):
    db_user = db.query(User).filter(
        User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return db_user
