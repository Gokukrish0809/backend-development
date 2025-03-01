"""
Test Suite for Book review API

This module contains test cases for the Book review API using FastAPI's `TestClient`
and pytest framework. It includes tests for authentication, review management, and edge cases.

Dependencies:
    - FastAPI TestClient for API testing
    - Pytest for unit testing and fixture management
    - SQLAlchemy for database interactions
    - JWT for authentication token handling
    - Threading for concurrency testing
"""
from fastapi import HTTPException
from fastapi.testclient import TestClient
from main import app
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, TEST_DATABASE_URL
from app.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from models.models import Base, Book, User, Review
from app.security import get_password_hash
from datetime import timedelta, datetime, timezone
from threading import Thread
from collections import defaultdict
import threading
import json
import jwt
import pytest
import logging
import time

# -----------------------------------
# Database Setup for Testing
# -----------------------------------
engine = create_engine(TEST_DATABASE_URL, isolation_level="SERIALIZABLE")
TestingSessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

@pytest.fixture(autouse=True)
def override_get_db(db_session: Session):
    """Override the database dependency to use a test session."""
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """Create test database tables before tests and drop them after tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Provide a database session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI TestClient for API interaction
client = TestClient(app)

def create_test_access_token(user: User):
    """
    Generate an access token for a user.

    Args:
        user (User): The user instance.

    Returns:
        str: A JWT access token.
    """
    payload = {
        "sub": user.email,
        "exp": int((datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@pytest.fixture(scope="function")
def setup_test_data(db_session: Session):
    """
    Pre-populates the test database with sample users, books, and reviews.

    Returns:
        dict: A dictionary containing test users and books.
    """

    # Clear existing data
    db_session.query(Review).delete()
    db_session.query(Book).delete()
    db_session.query(User).delete()
    db_session.commit()

    # Add sample users
    user1 = User(id=1, username="alice", email="alice@example.com", password_hash=get_password_hash("password123"))
    user2 = User(id=2, username="bob", email="bob@example.com", password_hash=get_password_hash("securepass"))
    db_session.add_all([user1, user2])
    db_session.commit()

    # Add sample books
    book1 = Book(id=1, title="The Great Gatsby", author="F. Scott Fitzgerald", review_count=0)
    book2 = Book(id=2, title="1984", author="George Orwell", review_count=0)
    book3 = Book(id=3, title="To Kill a Mockingbird", author="Harper Lee", review_count=0)
    book4 = Book(id=4, title="Pride and Prejudice", author="Jane Austen", review_count=0)
    book5 = Book(id=5, title="The Catcher in the Rye", author="J.D. Salinger", review_count=0)

    db_session.add_all([book1, book2, book3, book4, book5])
    db_session.commit()

    # Add sample reviews (more varied timestamps and users)
    review1 = Review(id=1, user_id=1, book_id=1, review_text="An amazing book! A must-read.", sentiment="positive", created_at=datetime.utcnow() - timedelta(days=2))
    review2 = Review(id=2, user_id=1, book_id=1, review_text="Amazing book!", sentiment="positive", created_at=datetime.utcnow() - timedelta(days=1))
    review3 = Review(id=3, user_id=2, book_id=2, review_text="This book changed my perspective on society.", sentiment="positive", created_at=datetime.utcnow() - timedelta(days=3))
    review4 = Review(id=4, user_id=1, book_id=3, review_text="I found it quite dull and overrated.", sentiment="negative", created_at=datetime.utcnow() - timedelta(days=4))
    review5 = Review(id=5, user_id=2, book_id=3, review_text="A deep and meaningful book.", sentiment="positive", created_at=datetime.utcnow() - timedelta(days=1))
    review6 = Review(id=6, user_id=1, book_id=4, review_text="A literary masterpiece!", sentiment="positive", created_at=datetime.utcnow() - timedelta(hours=12))
    review7 = Review(id=7, user_id=1, book_id=5, review_text="Not my cup of tea.", sentiment="negative", created_at=datetime.utcnow() - timedelta(days=5))
    review8 = Review(id=8, user_id=2, book_id=5, review_text="Absolutely fantastic!", sentiment="positive", created_at=datetime.utcnow() - timedelta(hours=3))
    review9 = Review(id=9, user_id=2, book_id=1, review_text="A classic that stands the test of time.", sentiment="positive", created_at=datetime.utcnow() - timedelta(minutes=30))

    db_session.add_all([review1, review2, review3, review4, review5, review6, review7, review8, review9])
    db_session.commit()

    return {
        "users": [user1, user2],
        "books": [book1, book2, book3, book4, book5],
        "reviews": [review1, review2, review3, review4, review5, review6, review7, review8, review9],
    }

###############################################################################
#                        Basic Functional Tests                             #
###############################################################################

def test_review_count(setup_test_data):
    test_data = setup_test_data
    assert len(test_data["reviews"]) == 9

def test_get_reviews_grouped_by_book(setup_test_data):
    response = client.get("/books/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)  # Ensure response is a list

    # Check that all books in test data are present in the response
    expected_books = {"The Great Gatsby", "1984", "To Kill a Mockingbird"}
    response_books = {book["book_title"] for book in data}

    assert expected_books.issubset(response_books)

    # Verify reviews structure inside each book
    for book in data:
        assert "book_id" in book
        assert "book_title" in book
        assert "book_author" in book
        assert "reviews" in book
        assert isinstance(book["reviews"], list)  # Reviews should be a list

        # If a book has reviews, validate the structure
        if book["reviews"]:
            first_review = book["reviews"][0]
            assert "id" in first_review
            assert "user_id" in first_review
            assert "book_id" in first_review
            assert "book_title" in first_review
            assert "book_author" in first_review
            assert "review_text" in first_review
            assert "sentiment" in first_review
            assert "created_at" in first_review

def test_get_reviews_one_book(setup_test_data):
    response = client.get("/books/review/1")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)  # Ensure response is a list
    assert data[0]["book_title"] == "The Great Gatsby"
    assert data[0]["book_author"] == "F. Scott Fitzgerald"
    assert data[0]["review_text"] == "An amazing book! A must-read."

def test_get_trending_books(setup_test_data):
    response = client.get("/books/trending/2")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

def test_create_review(setup_test_data):
    token = create_test_access_token(setup_test_data["users"][0])
    print(f"User: {setup_test_data['users'][0].email}")
    headers = {"Authorization": f"Bearer {token}"}

    print(f"Token: {token}")  # Check if token is being generated correctly
    print(headers)  # Ensure Authorization header is properly structured

    book_check = setup_test_data["books"]
    print([book.title for book in book_check])  # Print all book titles

    response = client.post("/review", headers=headers, json={"book_title": "The Great Gatsby", "book_author": "F. Scott Fitzgerald", "review_text": "Not so bad"})
    print(response)
    assert response.status_code == 200

    data = response.json()
    assert data["book_title"] == "The Great Gatsby"
    assert data["book_author"] == "F. Scott Fitzgerald"
    assert data["user_id"] == setup_test_data["users"][0].id 