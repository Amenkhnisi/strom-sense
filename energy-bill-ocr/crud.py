from sqlalchemy.orm import Session
from models import Invoice, User
from schemas import ParsedInvoiceData, UserCreate, UserLogin
from utils.utility_functions import normalize_field
from utils.auth import hash_password, verify_password
from fastapi import HTTPException
import re


# Register User

def register_user(user: UserCreate, db: Session):

    if len(user.username) < 8:
        raise HTTPException(
            status_code=400, detail="Username must be at least 8 characters")

    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=400, detail="Username already registered")

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
                    hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# Authenticate User

def authenticate_user(user: UserLogin, db: Session):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return db_user


# Get current user
def get_user(email: str, db: Session):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    return db_user

# Save bill data as invoice


def save_invoice_to_db(data: ParsedInvoiceData, db: Session) -> Invoice:
    billing_start, billing_end = normalize_field(
        data.billingPeriod, "billing_period")

    invoice = Invoice(
        supplier=data.supplier,
        supplier_raw=data.supplierName.raw if data.supplierName else None,
        supplier_confidence=data.supplierName.confidence if data.supplierName else None,

        customer_id=data.customerId.normalized if data.customerId else None,
        customer_raw=data.customerId.raw if data.customerId else None,
        customer_confidence=data.customerId.confidence if data.customerId else None,

        billing_start=billing_start,
        billing_end=billing_end,
        billing_raw=data.billingPeriod.raw if data.billingPeriod else None,
        billing_confidence=data.billingPeriod.confidence if data.billingPeriod else None,

        total_consumption=normalize_field(data.totalConsumption, "float"),
        consumption_raw=data.totalConsumption.raw if data.totalConsumption else None,
        consumption_confidence=data.totalConsumption.confidence if data.totalConsumption else None,

        total_amount=normalize_field(data.totalAmount, "float"),
        amount_raw=data.totalAmount.raw if data.totalAmount else None,
        amount_confidence=data.totalAmount.confidence if data.totalAmount else None,

        issue_date=normalize_field(data.issueDate, "date"),
        issue_raw=data.issueDate.raw if data.issueDate else None,
        issue_confidence=data.issueDate.confidence if data.issueDate else None,

        additional_fields=data.additionalFields or {}
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice
