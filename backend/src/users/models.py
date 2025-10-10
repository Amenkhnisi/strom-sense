from pydantic import BaseModel, EmailStr, constr


class UserResponse(BaseModel):
    username: str
    email: EmailStr
