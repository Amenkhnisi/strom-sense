from fastapi import APIRouter, Depends, Response, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserCreate, UserLogin, UserResponse
from crud import register_user, authenticate_user, get_user
from utils.auth import create_access_token, decode_access_token
import logging


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Register User
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = register_user(user, db)
        return {"message": "User registered", "id": new_user.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Authenticate User
@router.post("/login")
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    try:
        db_user = authenticate_user(user, db)
        token = create_access_token({"sub": db_user.email})

        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=3600,
            path="/"
        )
        return {"message": "Login successful"}

    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


# User logout
@router.post("/logout")
def logout(response: Response):
    try:
        response.delete_cookie("access_token", path="/")
        return {"message": "Logged out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Logout failed")


# Get current user
@router.get("/me")
def get_current_user(request: Request, db: Session = Depends(get_db)):
    try:
        user_email = decode_access_token(request)
        user = get_user(user_email, db)
        return UserResponse(username=user.username, email=user.email)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Not authenticated ")
