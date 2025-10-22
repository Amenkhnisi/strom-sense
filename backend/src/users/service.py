from fastapi import HTTPException, Request, Depends, status
from sqlalchemy.orm import Session

from src.ocr.models import BillMetricsResponse, UserBillWithMetrics
from src.ocr.service import MetricsService
from entities import UserBill, UserProfile, BillMetrics
from .models import UserProfileCreate, UserProfileUpdate, OverallSummary


from database.core import get_db
from jose import jwt, JWTError
from dotenv import load_dotenv
import os


load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")

# Get current user


def get_user(email: str, db: Session):
    db_user = db.query(UserProfile).filter(UserProfile.email == email).first()
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

# Create User


def createUser(
    user_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user profile
    """
    # Check if email already exists
    existing = db.query(UserProfile).filter(
        UserProfile.email == user_data.email
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = UserProfile(**user_data.dict())
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# Get user profile by ID
def getUser(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user profile by ID
    """
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    return user


# Get all users with pagination
def listUsers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all users with pagination
    """
    users = db.query(UserProfile).offset(skip).limit(limit).all()
    return users


# Update user profile
def updateUser(
    user_id: int,
    user_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user profile
    """
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Update only provided fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


# Delete user profile
def deleteUser(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a user and all associated data
    """
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Delete user (cascades to bills and anomalies)
    db.delete(user)
    db.commit()

    return {"message": f"User with ID {user_id} deleted successfully"}


# verify metrics
def verify_metrics(id: int, billYear: int, db: Session = Depends(get_db)):

    print("\n" + "="*60)
    print("🔍 METRICS VERIFICATION")
    print("="*60 + "\n")
    summary = []
    # Get a user with all 3 years of data
    user = db.query(UserProfile).filter(
        UserProfile.user_id == id
    ).first()

    if not user:
        print(f"❌ User with ID {id} not found!")
        raise HTTPException(
            status_code=404, detail=f"User with ID {id} not found!")

    for bill in sorted(user.bills, key=lambda b: b.bill_year):

        metrics = db.query(BillMetrics).filter(
            BillMetrics.bill_id == bill.id
        ).first()

        if metrics:

            if metrics.yoy_consumption_change_percent is not None:
                change = metrics.yoy_consumption_change_percent
                previous = metrics.previous_year_consumption_kwh

                # Calculate absolute difference
                diff = bill.consumption_kwh - metrics.previous_year_consumption_kwh

            metrics_response = BillMetricsResponse(
                id=metrics.id,
                bill_id=bill.id,
                days_in_billing_period=metrics.days_in_billing_period,
                daily_avg_consumption_kwh=metrics.daily_avg_consumption_kwh,
                cost_per_kwh=metrics.cost_per_kwh,
                yoy_consumption_change_percent=change if metrics.yoy_consumption_change_percent is not None else "N/A (first year)",
                previous_year_consumption_kwh=previous if metrics.previous_year_consumption_kwh else "N/A (first year)",
                difference_kwh=diff if metrics.previous_year_consumption_kwh else "YoY Change: N/A (first year)",
                calculated_at=metrics.calculated_at

            )

            bill_with_metrics = UserBillWithMetrics(
                id=bill.id,
                user_id=bill.user_id,
                bill_year=bill.bill_year,
                consumption_kwh=bill.consumption_kwh,
                total_cost_euros=bill.total_cost_euros,
                billing_start_date=bill.billing_start_date,
                billing_end_date=bill.billing_end_date,
                tariff_rate=bill.tariff_rate,
                uploaded_at=bill.uploaded_at,
                metrics=metrics_response.model_dump(exclude={"id", "bill_id"})
            )

            summary.append(bill_with_metrics.model_dump(
                exclude={"uploaded_at", "user_id"}))

        else:
            print(f"   ❌ No metrics found!")

    # Overall summary
    big_increases = db.query(BillMetrics, UserBill, UserProfile).join(
        UserBill, BillMetrics.bill_id == UserBill.id
    ).join(
        UserProfile, UserBill.user_id == UserProfile.user_id
    ).filter(
        UserBill.user_id == id,
        UserBill.bill_year == billYear,
        BillMetrics.yoy_consumption_change_percent.isnot(None)
    ).order_by(
        BillMetrics.yoy_consumption_change_percent.desc()
    ).limit(5).all()

    for i, (metrics, bill, user) in enumerate(big_increases, 1):
        change = metrics.yoy_consumption_change_percent

        overall_summary = OverallSummary(
            current_year=billYear,
            current_year_consumption_kwh=bill.consumption_kwh,
            previous_year=billYear - 1,
            previous_year_consumption_kwh=metrics.previous_year_consumption_kwh,
            yoy_change_percent=change,
            difference_kwh=bill.consumption_kwh - metrics.previous_year_consumption_kwh,
            cost_change_euros=round(
                (bill.total_cost_euros - (metrics.previous_year_consumption_kwh * bill.tariff_rate)), 2)
        )
        summary.append(overall_summary.model_dump())
    return summary

# Get dashboard summary for a user


def getUserDashboard(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get dashboard summary for a user
    """
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Get latest bill
    latest_bill = db.query(UserBill).filter(
        UserBill.user_id == user_id
    ).order_by(UserBill.bill_year.desc()).first()

    # Get active anomalies (not dismissed)
    from entities import AnomalyDetection
    active_anomalies = db.query(AnomalyDetection).filter(
        AnomalyDetection.user_id == user_id,
        AnomalyDetection.is_dismissed == False
    ).all()

    # Count total bills
    total_bills = db.query(UserBill).filter(
        UserBill.user_id == user_id).count()
    # Return summary
    summary = verify_metrics(user_id, latest_bill.bill_year, db)

    return {
        "user": user,
        "latest_bill": latest_bill,
        "active_anomalies": active_anomalies,
        "total_bills_count": total_bills,
        "metrics_summary": summary
    }


# Calculate metrics for all bills of a user
def calculatUserMetrics(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Calculate metrics for all bills of a user
    """
    user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    metrics_service = MetricsService(db)
    result = metrics_service.calculate_for_user(user_id)

    return {
        "message": f"Metrics calculated for user {user_id}",
        "stats": result
    }
