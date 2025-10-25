from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from .models import UserCreate, UserLogin
from .service import register_user, authenticate_user, create_access_token
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["Authentication"])


# Register User
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = register_user(user, db)
        return {"message": "User registered", "id": new_user.user_id}
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
