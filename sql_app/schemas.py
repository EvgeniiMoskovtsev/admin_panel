from pydantic import BaseModel
from datetime import datetime
import enum


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class UserCreate(BaseModel):
    email: str
    name: str
    password: str

class UserOut(BaseModel):
    email: str
    name: str


class User(UserCreate):
    id: int

    class Config:
        from_attributes = True


class UserAuthenticate(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str


class UserStatusUpdate(BaseModel):
    status: UserStatus
