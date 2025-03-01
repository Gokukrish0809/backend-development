from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.security import create_access_token, verify_password, get_password_hash, oauth2_scheme
from schemas.schemas import UserCreate, UserLogin, UserResponse
from app.database import get_db
from models.models import User

router = APIRouter(
    prefix = "/auth",
    tags = ["Authentication"]
)

@router.post("/register", response_model = UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code = 400, detail = "A user already exists with this email")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(username = user_data.username, email = user_data.email, password_hash = hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid credentials")

    access_token = create_access_token(data = {"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

