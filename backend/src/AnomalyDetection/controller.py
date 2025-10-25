"""
controllers/anomaly_controller.py
API routes for anomaly detection
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from .service import AnomalyDetectionService
from .schemas import AnomalyDetectionResponse, AnomalyDismissRequest


router = APIRouter(
    prefix="/anomalies",
    tags=["Anomaly Detection"]
)


@router.post("/detect/{bill_id}")
def detect_anomalies(
    bill_id: int,
    save_result: bool = Query(
        True, description="Save detection result to database"),
    db: Session = Depends(get_db)
):
    """
    Run anomaly detection on a specific bill.

    Runs all three detectors (historical, peer, predictive) and combines results.

    Example: POST /anomalies/detect/1?save_result=true
    """

    service = AnomalyDetectionService(db)
    result = service.detect_all_anomalies(bill_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} not found"
        )

    # Save to database if requested
    if save_result and result['has_anomaly']:
        anomaly = service.save_anomaly_detection(result)
        result['anomaly_id'] = anomaly.id

    return result


@router.post("/detect/user/{user_id}")
def detect_user_anomalies(
    user_id: int,
    year: int = Query(..., description="Year to check"),
    save_results: bool = Query(True, description="Save detection results"),
    db: Session = Depends(get_db)
):
    """
    Run anomaly detection on all bills for a user in a specific year.

    Example: POST /anomalies/detect/user/1?year=2024
    """

    from entities import UserBill

    # Get user's bills for the year
    bills = db.query(UserBill).filter(
        UserBill.user_id == user_id,
        UserBill.bill_year == year
    ).all()

    if not bills:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No bills found for user {user_id} in year {year}"
        )

    service = AnomalyDetectionService(db)
    results = []

    for bill in bills:
        result = service.detect_all_anomalies(bill.id)
        if result:
            if save_results and result['has_anomaly']:
                anomaly = service.save_anomaly_detection(result)
                result['anomaly_id'] = anomaly.id
            results.append(result)

    anomalies_found = sum(1 for r in results if r['has_anomaly'])

    return {
        "user_id": user_id,
        "year": year,
        "total_bills_checked": len(results),
        "anomalies_found": anomalies_found,
        "results": results
    }


@router.get("/user/{user_id}", response_model=List[AnomalyDetectionResponse])
def get_user_anomalies(
    user_id: int,
    only_active: bool = Query(
        True, description="Only show non-dismissed anomalies"),
    db: Session = Depends(get_db)
):
    """
    Get all anomalies for a specific user.

    Example: GET /anomalies/user/1?only_active=true
    """

    service = AnomalyDetectionService(db)
    anomalies = service.get_user_anomalies(user_id, only_active)

    if not anomalies:
        return []

    return anomalies


@router.get("/{anomaly_id}", response_model=AnomalyDetectionResponse)
def get_anomaly(
    anomaly_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific anomaly.

    Example: GET /anomalies/123
    """

    from entities import AnomalyDetection

    anomaly = db.query(AnomalyDetection).filter(
        AnomalyDetection.id == anomaly_id
    ).first()

    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID {anomaly_id} not found"
        )

    return anomaly


@router.post("/{anomaly_id}/dismiss")
def dismiss_anomaly(
    anomaly_id: int,
    request: AnomalyDismissRequest = None,
    db: Session = Depends(get_db)
):
    """
    Dismiss an anomaly (mark as acknowledged by user).

    Example: POST /anomalies/123/dismiss

    Optional body:
    {
      "feedback": "helpful" or "not_helpful" or "false_positive"
    }
    """

    service = AnomalyDetectionService(db)

    feedback = request.feedback if request else None
    anomaly = service.dismiss_anomaly(anomaly_id, feedback)

    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly with ID {anomaly_id} not found"
        )

    return {
        "message": "Anomaly dismissed successfully",
        "anomaly_id": anomaly_id,
        "dismissed_at": anomaly.dismissed_at,
        "feedback": feedback
    }


@router.get("/bill/{bill_id}/check")
def check_bill_for_anomaly(
    bill_id: int,
    db: Session = Depends(get_db)
):
    """
    Check if a bill has any detected anomalies.

    Returns existing anomaly detection if available, otherwise runs new detection.

    Example: GET /anomalies/bill/1/check
    """

    from entities import AnomalyDetection

    # Check if anomaly already exists
    existing = db.query(AnomalyDetection).filter(
        AnomalyDetection.bill_id == bill_id
    ).first()

    if existing:
        return {
            "has_existing_detection": True,
            "anomaly": AnomalyDetectionResponse.model_validate(existing)
        }

    # Run new detection
    service = AnomalyDetectionService(db)
    result = service.detect_all_anomalies(bill_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with ID {bill_id} not found"
        )

    return {
        "has_existing_detection": False,
        "detection_result": result
    }


@router.get("/stats/overview")
def get_anomaly_statistics(
    year: int = Query(None, description="Filter by year"),
    db: Session = Depends(get_db)
):
    """
    Get overall anomaly detection statistics.

    Example: GET /anomalies/stats/overview?year=2024
    """

    from entities import AnomalyDetection
    from sqlalchemy import func

    query = db.query(AnomalyDetection)

    if year:
        from entities import UserBill
        query = query.join(UserBill).filter(UserBill.bill_year == year)

    # Total anomalies
    total = query.count()

    # By severity
    by_severity = db.query(
        AnomalyDetection.severity_level,
        func.count(AnomalyDetection.id)
    ).group_by(AnomalyDetection.severity_level).all()

    # By type
    by_type = db.query(
        AnomalyDetection.anomaly_type,
        func.count(AnomalyDetection.id)
    ).group_by(AnomalyDetection.anomaly_type).all()

    # Active vs dismissed
    active = query.filter(AnomalyDetection.is_dismissed == False).count()
    dismissed = query.filter(AnomalyDetection.is_dismissed == True).count()

    return {
        "total_anomalies": total,
        "active": active,
        "dismissed": dismissed,
        "by_severity": {sev: count for sev, count in by_severity},
        "by_type": {anom_type: count for anom_type, count in by_type},
        "year": year or "all"
    }


@router.post("/batch-detect")
def batch_detect_anomalies(
    year: int = Query(..., description="Year to process"),
    only_new: bool = Query(
        True, description="Skip bills with existing detections"),
    db: Session = Depends(get_db)
):
    """
    Batch process anomaly detection for all bills in a year.

    Useful for processing historical data or running scheduled checks.

    Example: POST /anomalies/batch-detect?year=2024&only_new=true
    """

    from entities import UserBill, AnomalyDetection

    # Get all bills for the year
    bills = db.query(UserBill).filter(UserBill.bill_year == year).all()

    if not bills:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No bills found for year {year}"
        )

    service = AnomalyDetectionService(db)

    processed = 0
    skipped = 0
    anomalies_found = 0
    errors = 0

    for bill in bills:
        try:
            # Skip if already has detection
            if only_new:
                existing = db.query(AnomalyDetection).filter(
                    AnomalyDetection.bill_id == bill.id
                ).first()

                if existing:
                    skipped += 1
                    continue

            # Run detection
            result = service.detect_all_anomalies(bill.id)

            if result:
                processed += 1

                if result['has_anomaly']:
                    service.save_anomaly_detection(result)
                    anomalies_found += 1

        except Exception as e:
            print(f"Error processing bill {bill.id}: {e}")
            errors += 1

    return {
        "message": "Batch detection complete",
        "year": year,
        "total_bills": len(bills),
        "processed": processed,
        "skipped": skipped,
        "anomalies_found": anomalies_found,
        "errors": errors
    }
