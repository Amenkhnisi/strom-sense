from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.security.api_key import APIKeyHeader


security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.environ.get("API_USER")
    correct_password = os.environ.get("API_PASSWORD")

    if not (correct_username and correct_password):
        # 👇 This header triggers the browser popup
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"}  # ✅ This triggers the popup
        )

    return credentials.username
