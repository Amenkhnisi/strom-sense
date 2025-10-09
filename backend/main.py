from fastapi import FastAPI
from routes import upload_bill
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="AI-Powered Home Energy Optimizer", version="1.0.0")

app.include_router(upload_bill.router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def health():
    return {"message": "StromSense backend is running"}
