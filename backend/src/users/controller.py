"""
API routes for user-related operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from .models import (
    UserProfileCreate,
    UserProfileResponse,
    UserProfileUpdate,
    DashboardSummary,
)
from .service import decode_access_token, deleteUser, get_user, createUser, getUser, getUserDashboard, listUsers, updateUser, calculatUserMetrics


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Get current user


@router.get("/me")
def get_current_user(request: Request, db: Session = Depends(get_db)):
    try:
        user_email = decode_access_token(request)
        user = get_user(user_email, db)
        return UserProfileResponse(user_id=user.user_id,
                                   email=user.email,
                                   username=user.username,
                                   postal_code=user.postal_code,
                                   household_size=user.household_size,
                                   property_type=user.property_type,
                                   property_size_sqm=user.property_size_sqm,
                                   created_at=user.created_at)
    except HTTPException as e:
        raise e
    except Exception as e:
        print("Error retrieving current user:", e)  # Debug print
        raise HTTPException(status_code=500, detail="Not authenticated ")


@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user profile
    """
    return createUser(user_data, db)


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user profile by ID
    """

    return getUser(user_id, db)


@router.get("/", response_model=List[UserProfileResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all users with pagination
    """

    return listUsers(skip, limit, db)


@router.patch("/{user_id}", response_model=UserProfileResponse)
def update_user(
    user_id: int,
    user_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user profile
    """

    return updateUser(user_id, user_data, db)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a user and all associated data
    """

    return deleteUser(user_id, db)


@router.get("/{user_id}/dashboard", response_model=DashboardSummary)
def get_user_dashboard(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get dashboard summary for a user
    """

    return getUserDashboard(user_id, db)


@router.post("/{user_id}/calculate-all-metrics")
def calculate_user_metrics(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Calculate metrics for all bills of a user
    """
    return calculatUserMetrics(user_id, db)
