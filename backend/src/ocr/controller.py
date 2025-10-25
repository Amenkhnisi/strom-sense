"""
API routes for bill-related operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from entities import UserBill, BillMetrics
from .models import (
    UserBillCreate,
    UserBillResponse,
    UserBillWithMetrics,
    BillMetricsResponse
)
from .service import MetricsService


router = APIRouter(
    prefix="/bills",
    tags=["Bills"]
)


@router.post("/", response_model=UserBillResponse, status_code=status.HTTP_201_CREATED)
def create_bill(
    bill_data: UserBillCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new bill (from OCR extraction)
    """
    # Create bill
    bill = UserBill(**bill_data.dict())
    db.add(bill)
    db.commit()
    db.refresh(bill)

    # Calculate metrics automatically
    metrics_service = MetricsService(db)
    metrics_service.calculate_for_bill(bill.id)

    return bill


@router.get("/{bill_id}", response_model=UserBillWithMetrics)
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a bill by ID with its metrics
    """
    bill = db.query(UserBill).filter(UserBill.id == bill_id).first()

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} not found"
        )

    # Get metrics
    metrics = db.query(BillMetrics).filter(
        BillMetrics.bill_id == bill_id).first()

    # Convert to response model
    bill_dict = UserBillResponse.model_validate(
        bill).model_dump()
    bill_dict["metrics"] = BillMetricsResponse.model_validate(
        metrics).model_dump(exclude={"difference_kwh", "yoy_consumption_change_percent"}) if metrics else None

    return bill_dict


@router.get("/user/{user_id}", response_model=List[UserBillResponse])
def get_user_bills(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all bills for a specific user
    """
    bills = db.query(UserBill).filter(
        UserBill.user_id == user_id
    ).order_by(UserBill.bill_year.desc()).all()

    if not bills:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No bills found for user {user_id}"
        )

    return bills


@router.post("/{bill_id}/calculate-metrics", response_model=BillMetricsResponse)
def calculate_bill_metrics(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """
    Calculate or recalculate metrics for a specific bill
    """
    metrics_service = MetricsService(db)
    metrics = metrics_service.calculate_for_bill(bill_id)

    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} not found"
        )

    return metrics


@router.get("/{bill_id}/metrics", response_model=BillMetricsResponse)
def get_bill_metrics(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """
    Get calculated metrics for a bill
    """
    metrics = db.query(BillMetrics).filter(
        BillMetrics.bill_id == bill_id).first()

    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metrics found for bill {bill_id}. Try calculating them first."
        )

    return metrics


@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a bill and its associated metrics
    """
    bill = db.query(UserBill).filter(UserBill.id == bill_id).first()

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} not found"
        )

    # Delete associated metrics first (if any)
    db.query(BillMetrics).filter(BillMetrics.bill_id == bill_id).delete()

    # Delete bill
    db.delete(bill)
    db.commit()

    return None
