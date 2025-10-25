from fastapi import FastAPI
from auth import auth_router
from users import users_router
from ocr import ocr_router
from weather import weather_router
from PeerStatistics import peer_statistics_router
from AnomalyDetection import anomaly_detection_router
from dotenv import load_dotenv
import os

load_dotenv()


def register_routes(app: FastAPI, api_version: str = os.environ.get("API_VERSION", "/api/v1")):
    app.include_router(auth_router, prefix=api_version)
    app.include_router(users_router, prefix=api_version)
    app.include_router(ocr_router, prefix=api_version)
    app.include_router(weather_router, prefix=api_version)
    app.include_router(peer_statistics_router, prefix=api_version)
    app.include_router(anomaly_detection_router, prefix=api_version)
