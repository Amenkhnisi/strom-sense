from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from src.database.core import get_db
from .service import decode_access_token, get_user
from .models import UserResponse


router = APIRouter(prefix="/users", tags=["Users"])


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
