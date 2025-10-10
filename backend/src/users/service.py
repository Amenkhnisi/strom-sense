from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from src.entities.user import User
from jose import jwt, JWTError
from dotenv import load_dotenv
import os


load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")

# Get current user


def get_user(email: str, db: Session):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    return db_user

# Check authenticated User


def decode_access_token(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
