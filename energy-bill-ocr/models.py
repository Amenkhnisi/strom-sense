from sqlalchemy import Column, Integer, String, Float, Date, JSON
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    supplier = Column(String, nullable=False)
    supplier_raw = Column(String)
    supplier_confidence = Column(Float)

    customer_id = Column(String)
    customer_raw = Column(String)
    customer_confidence = Column(Float)

    billing_start = Column(Date)
    billing_end = Column(Date)
    billing_raw = Column(String)
    billing_confidence = Column(Float)

    total_consumption = Column(Float)
    consumption_raw = Column(String)
    consumption_confidence = Column(Float)

    total_amount = Column(Float)
    amount_raw = Column(String)
    amount_confidence = Column(Float)

    issue_date = Column(Date)
    issue_raw = Column(String)
    issue_confidence = Column(Float)

    additional_fields = Column(JSON)
