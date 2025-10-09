from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas import ParsedInvoiceData
from crud import save_invoice_to_db
from database import get_db

route = APIRouter(tags=["Save Data"])


@route.post("/save-invoice")
def save_invoice(data: ParsedInvoiceData, db: Session = Depends(get_db)):
    invoice = save_invoice_to_db(data, db)
    return {"message": "Invoice saved", "id": invoice.id}
