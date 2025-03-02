from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ------------------- USER SCHEMAS -------------------

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

# ------------------- BOOK SCHEMAS -------------------

class BookBase(BaseModel):
    title: str
    author: str
    review_count: int = 0  # Default to 0

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: int

    class Config:
        from_attributes = True

# ------------------- REVIEW SCHEMAS -------------------

class ReviewBase(BaseModel):
    book_title: str
    book_author: str
    review_text: str = Field(..., max_length=5000)  # Enforce 5000-character limit

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(ReviewBase):
    id: int

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    book_title: str
    book_author: str
    review_text: str
    sentiment: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReviewResponseGrouped(BaseModel):
    id: int
    user_id: int
    review_text: str
    sentiment: str
    created_at: Optional[datetime] = None


# ------------------- BOOK WITH REVIEWS RESPONSE -------------------

class BookWithReviewsResponse(BaseModel):
    book_id: int
    book_title: str
    book_author: str
    reviews: List[ReviewResponseGrouped]