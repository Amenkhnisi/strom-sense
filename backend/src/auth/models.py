from pydantic import BaseModel, EmailStr, constr
from typing import Annotated


# Pydantic Models

class UserCreate(BaseModel):
    username: Annotated[str, constr(min_length=5, max_length=16)]
    email: EmailStr
    password: Annotated[str, constr(min_length=8, max_length=72)]
    postal_code: Annotated[int, constr(min_length=5, max_length=5)]


class UserLogin(BaseModel):
    email: EmailStr
    password: Annotated[str, constr(min_length=8, max_length=72)]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
