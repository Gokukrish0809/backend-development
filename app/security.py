from datetime import datetime,timedelta
from passlib.context import CryptContext
import jwt
from fastapi.security import OAuth2PasswordBearer
from config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from app.database import get_db
from models.models import User
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/auth/login")

def create_access_token(data:dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid authentication token")

        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "user not found")

        return user
    except:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid authentication token")


