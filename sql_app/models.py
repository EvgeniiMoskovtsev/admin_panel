from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
import enum
from .database import Base


class UserStatus(str, enum.Enum):
    """
    User status represents is user blocked or not
    """
    ACTIVE = "active"
    BLOCKED = "blocked"

class User(Base):
    """
    User model represents the users in the system.
    - id: Unique identifier for the user.
    - name: Name of the user.
    - email: Email address of the user, used for authentication.
    - hashed_password: Securely stored password hash.
    - created_at: The date and time when the user account was created.
    - last_login: The date and time of the user's last login.
    - status: Account status, can be either 'active' or 'blocked'.
    """
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, nullable=False)
    email           = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.now)
    last_login      = Column(DateTime, default=datetime.now)
    status          = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
