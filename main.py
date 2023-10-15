from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from starlette.requests import Request

from sqlalchemy.orm import Session
from sql_app import crud, models, schemas
from sql_app.database import SessionLocal, Base, engine

from datetime import timedelta, datetime
from jose import JWTError, jwt
import secrets

import logging
logging.basicConfig(level=logging.INFO)

templates = Jinja2Templates(directory="html")
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    logging.info(f"Token: {token}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        logging.info(f"Payload: {payload}")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

@app.on_event("startup")  # Это событие запустится при старте приложения
async def startup_event():
    Base.metadata.create_all(bind=engine)

@app.post("/login/", response_model=schemas.Token)
async def login_for_access_token(form_data: schemas.UserAuthenticate, db: Session = Depends(get_db)):
    logging.info(f"Trying to authenticate user with email: {form_data.email}")
    user = crud.authenticate_user(db, email=form_data.email, password=form_data.password)
    if not user:
        logging.warning(f"Failed to authenticate user with email: {form_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    logging.info(f"Authenticated user with email: {form_data.email} and generated token")
    return {"access_token": access_token, "token_type": "bearer"}



@app.get("/register/", response_class=HTMLResponse)
async def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login/", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/register/", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        created_user = crud.create_user(db=db, user=user)
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while registering the user.")
    return schemas.UserOut(email=created_user.email, name=created_user.name)



@app.get("/users/", response_class=HTMLResponse)
async def read_users(request: Request, current_user: models.User = Depends(get_current_user),
                     skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    logging.info("Try get_users")
    users = crud.get_users(db, skip=skip, limit=limit)
    return templates.TemplateResponse("users.html", {"request": request, "users": users})


@app.patch("/users/{user_id}/status/", response_model=schemas.User)
def update_status(user_id: int, status_update: schemas.UserStatusUpdate, db: Session = Depends(get_db)):
    updated_user = crud.update_user_status(db, user_id, status_update.status)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@app.delete("/users/{user_id}/", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    deleted_user = crud.delete_user(db, user_id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
