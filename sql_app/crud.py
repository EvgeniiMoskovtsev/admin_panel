from sqlalchemy.orm import Session
from . import models, schemas
import hashlib


def get_password_hash(password: str):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def verify_password(plain_password: str, hashed_password: str):
    return get_password_hash(plain_password) == hashed_password


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, name=user.name, hashed_password=hashed_password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        # Закрываем сессию
        db.close()

    return db_user

def update_user_status(db: Session, user_id: int, new_status: models.UserStatus):
    user = get_user(db, user_id)
    if user:
        user.status = new_status
        db.commit()
        db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if user:
        db.delete(user)
        db.commit()
    return user