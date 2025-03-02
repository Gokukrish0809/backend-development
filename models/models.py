from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    username = Column(String, unique = True, nullable = False)
    email = Column(String, unique = True, nullable = False)
    password_hash = Column(String, nullable = False)

    #relationships
    reviews = relationship("Review", back_populates = "user")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key = True, index = True)
    title = Column(String, nullable = False)
    author = Column(String, nullable = False)
    review_count = Column(Integer, default = 0)

    #relationships
    reviews = relationship("Review", back_populates = "book")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable = False)
    review_text = Column(String, nullable = False)
    sentiment = Column(String, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)
    
    #enforce unique constraint to prevent the same user from reviewing the same book
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="user_book_review_uc"),)

    #realtionships
    user = relationship("User", back_populates = "reviews")
    book = relationship("Book", back_populates = "reviews")