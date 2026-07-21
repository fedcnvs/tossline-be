from pydantic import BaseModel, EmailStr


class RequestPinIn(BaseModel):
    email: EmailStr


class VerifyPinIn(BaseModel):
    email: EmailStr
    pin: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    level: str

    model_config = {"from_attributes": True}
