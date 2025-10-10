from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import register_routes


app = FastAPI(title="AI-Powered Home Energy Optimizer", version="1.0.0")

register_routes(app=app)

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
