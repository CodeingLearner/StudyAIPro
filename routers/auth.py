import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from services.db import get_db, Base, engine
from models.user import User
from jose import JWTError, jwt

SECRET_KEY = os.getenv("STUDYAI_SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

router = APIRouter()


class RegisterIn(BaseModel):
    username: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def create_tables():
    Base.metadata.create_all(bind=engine)


def verify_password(plain, stored):
    # Simple plain text comparison
    return plain == stored


def get_password_hash(password):
    # Store password as-is (plain text)
    return password


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/register", response_model=Token)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    # create tables on first call
    create_tables()
    try:
        user = db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first()
        if user:
            raise HTTPException(status_code=400, detail="User already exists")
        new = User(username=payload.username, email=payload.email, hashed_password=payload.password)
        db.add(new)
        db.commit()
        db.refresh(new)
        token = create_access_token({"sub": new.username})
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=Token)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == payload.username).first()
        if not user or payload.password != user.hashed_password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token({"sub": user.username})
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")
