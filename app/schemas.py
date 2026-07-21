from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RequestPinIn(BaseModel):
    email: EmailStr


class VerifyPinIn(BaseModel):
    email: EmailStr
    pin: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str | None = None
    level: str

    model_config = {"from_attributes": True}


class VideoOpenIn(BaseModel):
    video_name: str = Field(min_length=1, max_length=500)
    source: Literal["cloudflare", "desktop"] = "cloudflare"
