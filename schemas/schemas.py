from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

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

class BookBase(BaseModel):
    title: str
    author: str
    review_count: Optional[int] = 0

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: int

    class Config:
        from_attributes = True

class ReviewCreate(BaseModel):
    book_title: str
    book_author: str
    review_text: str

class ReviewUpdate(BaseModel):
    id: int
    book_title: str
    book_author: str
    review_text: str

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

class BookWithReviewsResponse(BaseModel):
    book_id: int
    book_title: str
    book_author: str
    reviews: List[ReviewResponse]
