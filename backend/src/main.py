from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api import register_routes
from sqlalchemy.orm import Session
from database.core import get_db


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


# Health check endpoint
@app.get("/", tags=["Health"])
def root():
    """API health check"""
    return {
        "status": "online",
        "message": "Energy Bills API is running",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """
    Detailed health check including database connection
    """
    try:
        # Test database query
        from src.entities.user import UserProfile
        user_count = db.query(UserProfile).count()

        return {
            "status": "healthy",
            "database": "connected",
            "users_count": user_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
