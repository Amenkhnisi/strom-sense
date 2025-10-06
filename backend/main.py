from fastapi import FastAPI
from routes import upload_bill

app = FastAPI(title="AI-Powered Home Energy Optimizer", version="1.0.0")

app.include_router(upload_bill.router)


@app.get("/", tags=["Health"])
def health():
    return {"message": "StromSense backend is running"}
