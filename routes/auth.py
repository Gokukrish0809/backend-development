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
    """
    Register a new user in the system.

    This endpoint creates a new user account after verifying that the provided email
    is not already associated with an existing user. The password is securely hashed 
    before being stored in the database.

    Args:
        user_data (UserCreate): The user details including username, email, and password.
        db (Session): Database session dependency.

    Raises:
        HTTPException: If a user with the provided email already exists.

    Returns:
        UserResponse: The newly created user object.
    """
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
    """
    Authenticate a user and generate an access token.

    This endpoint verifies user credentials and returns a JWT access token
    if the provided email and password match a registered user.

    Args:
        login_data (UserLogin): The user's email and password.
        db (Session): Database session dependency.

    Raises:
        HTTPException: If the credentials are invalid (wrong email or password).

    Returns:
        dict: A dictionary containing the access token and token type.
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid credentials")

    access_token = create_access_token(data = {"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

