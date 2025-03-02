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
from sqlalchemy.sql import text
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

def create_test_access_token(user: User, exp: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    """
    Generate an access token for a user.

    Args:
        user (User): The user instance.

    Returns:
        str: A JWT access token.
    """
    payload = {
        "sub": user.email,
        "exp": int((datetime.utcnow() + timedelta(minutes=exp)).timestamp())
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

    # Reset auto-increment sequences (PostgreSQL & SQLite)
    if engine == "sqlite":
        db_session.execute(text("DELETE FROM sqlite_sequence WHERE name='review';"))
        db_session.execute(text("DELETE FROM sqlite_sequence WHERE name='book';"))
        db_session.execute(text("DELETE FROM sqlite_sequence WHERE name='user';"))
    elif engine == "postgresql":
        db_session.execute(text("ALTER SEQUENCE review_id_seq RESTART WITH 1;"))
        db_session.execute(text("ALTER SEQUENCE book_id_seq RESTART WITH 1;"))
        db_session.execute(text("ALTER SEQUENCE user_id_seq RESTART WITH 1;"))

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
    book6 = Book(id=6, title="Moby-Dick", author="Herman Melville", review_count=0)
    book7 = Book(id=7, title="Brave New World", author="Aldous Huxley", review_count=0)

    db_session.add_all([book1, book2, book3, book4, book5, book6, book7])
    db_session.commit()

    # Add sample reviews (more varied timestamps and users)
    review1 = Review(user_id=1, book_id=1, review_text="An amazing book! A must-read.", sentiment="positive", created_at=datetime.utcnow() - timedelta(days=2))
    review2 = Review(user_id=1, book_id=2, review_text="Amazing book!", sentiment="positive", created_at=datetime.utcnow() - timedelta(days=1))
    review3 = Review(user_id=2, book_id=2, review_text="This book changed my perspective on society.", sentiment="positive", created_at=datetime.utcnow() - timedelta(days=3))
    review4 = Review(user_id=1, book_id=3, review_text="I found it quite dull and overrated.", sentiment="negative", created_at=datetime.utcnow() - timedelta(days=4))
    review5 = Review(user_id=2, book_id=3, review_text="A deep and meaningful book.", sentiment="positive", created_at=datetime.utcnow() - timedelta(days=1))
    review6 = Review(user_id=1, book_id=4, review_text="A literary masterpiece!", sentiment="positive", created_at=datetime.utcnow() - timedelta(hours=12))
    review7 = Review(user_id=1, book_id=5, review_text="Not my cup of tea.", sentiment="negative", created_at=datetime.utcnow() - timedelta(days=5))
    review8 = Review(user_id=2, book_id=5, review_text="Absolutely fantastic!", sentiment="positive", created_at=datetime.utcnow() - timedelta(hours=3))
    review9 = Review(user_id=2, book_id=1, review_text="A classic that stands the test of time.", sentiment="positive", created_at=datetime.utcnow() - timedelta(minutes=30))

    db_session.add_all([review1, review4, review5, review6, review7, review8, review9])
    db_session.commit()

    return {
        "users": [user1, user2],
        "books": [book1, book2, book3, book4, book5, book6, book7],
        "reviews": [review1, review4, review5, review6, review7, review8, review9],
    }

###############################################################################
#                        Basic Functional Tests                             #
###############################################################################

def test_review_count(setup_test_data):
    test_data = setup_test_data
    assert len(test_data["reviews"]) == 7

def test_get_reviews_grouped_by_book(setup_test_data):
    response = client.get("/books/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)  # Ensure response is a list

    # Check that all books in test data are present in the response
    expected_books = {"The Great Gatsby", "To Kill a Mockingbird", "Pride and Prejudice", "The Catcher in the Rye"}
    response_books = {book["book_title"] for book in data}

    assert response_books == expected_books

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
            assert "review_text" in first_review
            assert "sentiment" in first_review
            assert "created_at" in first_review

def test_get_reviews_one_book(setup_test_data):
    response = client.get("/books/review/1")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)  # Ensure response is a list
    assert data[0]["review_text"] == "An amazing book! A must-read."
    assert len(data) == 2

def test_get_trending_books(setup_test_data):
    response = client.get("/books/trending/2")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

def test_create_review(setup_test_data):
    token = create_test_access_token(setup_test_data["users"][1])
    headers = {"Authorization": f"Bearer {token}"}

    print(f"Token: {token}")  # Check if token is being generated correctly
    print(headers)  # Ensure Authorization header is properly structured

    book_check = setup_test_data["books"]
    print([book.title for book in book_check])  # Print all book titles

    response = client.post("/books/review/", headers=headers, json={"book_title": "Pride and Prejudice", "book_author": "Jane Austen", "review_text": "This book changed my whole perspective on life"})
    print(response)
    assert response.status_code == 200

    data = response.json()
    assert data["book_title"] == "Pride and Prejudice"
    assert data["book_author"] == "Jane Austen"
    assert data["user_id"] == setup_test_data["users"][1].id 

###############################################################################
#                          Security Tests                            #
###############################################################################

def test_unauthorized_access(setup_test_data):
    """Test API endpoints without authentication."""
    response = client.post("/books/review/", json={"book_title": "The Great Gatsby", "review_text": "Unauthorized review"})
    assert response.status_code == 401  # Unauthorized

def test_expired_token(setup_test_data):
    """Test API behavior with an expired JWT token."""
    token = create_test_access_token(setup_test_data["users"][0], exp=-1)  # Expired token
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/books/review/", headers=headers, json={"book_title": "The Great Gatsby", "review_text": "Should fail"})
    assert response.status_code == 401  # Unauthorized

def test_tampered_token(setup_test_data):
    """Test API behavior with a tampered JWT token."""
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid_payload.signature"
    headers = {"Authorization": f"Bearer {fake_token}"}

    response = client.post("/books/review/", headers=headers, json={"book_title": "The Great Gatsby", "review_text": "Tampered token"})
    assert response.status_code == 401  # Unauthorized

###############################################################################
#                          Edge Case Tests                                   #
###############################################################################

def test_sql_injection_attempt(setup_test_data):
    """Ensure review text is properly sanitized and does not allow SQL injection."""
    token = create_test_access_token(setup_test_data["users"][0])
    headers = {"Authorization": f"Bearer {token}"}

    malicious_payload = {
        "book_title": "1984",
        "book_author": "George Orwell",
        "review_text": "'); DROP TABLE reviews; --"
    }
    response = client.post("/books/review/", headers=headers, json=malicious_payload)
    assert response.status_code == 400  # Should be rejected

def test_duplicate_review_prevention(setup_test_data):
    """Ensure a user cannot post identical reviews for the same book."""
    token = create_test_access_token(setup_test_data["users"][1])
    headers = {"Authorization": f"Bearer {token}"}

    review_payload = {
        "book_title": "1984",
        "book_author": "George Orwell",
        "review_text": "This book is amazing!"
    }

    # First submission (should succeed)
    response1 = client.post("/books/review/", headers=headers, json=review_payload)
    assert response1.status_code == 200

    # Second identical submission (should be rejected)
    response2 = client.post("/books/review/", headers=headers, json=review_payload)
    assert response2.status_code == 400

def test_large_review_text(setup_test_data):
    """Ensure the API correctly handles large review texts."""
    token = create_test_access_token(setup_test_data["users"][0])
    headers = {"Authorization": f"Bearer {token}"}

    long_review = "A" * 1001  # Exceeding the 1000 character limit
    response = client.post("/books/review/", headers=headers, json={"book_title": "The Great Gatsby", "book_author": "George Orwell", "review_text": long_review})
    assert response.status_code == 400  # Should reject oversized text

def test_non_existent_book_review(setup_test_data):
    """Test posting a review for a book that doesn't exist."""
    token = create_test_access_token(setup_test_data["users"][0])
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/books/review/", headers=headers, json={"book_title": "Unknown Book", "book_author": "Unknown author", "review_text": "Review for a non-existent book"})
    assert response.status_code == 404  # Not Found

###############################################################################
#                          Concurrency Tests                                #
###############################################################################

def test_concurrent_review_submission(setup_test_data):
    """Ensure multiple users can submit reviews concurrently without issues."""
    token1 = create_test_access_token(setup_test_data["users"][0])
    token2 = create_test_access_token(setup_test_data["users"][1])
    
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    review_payload1 = {"book_title": "Moby-Dick", "book_author": "Herman Melville", "review_text": "Great book!"}
    review_payload2 = {"book_title": "Brave New World", "book_author": "Aldous Huxley", "review_text": "Loved it!"}

    results = []

    def submit_review(headers, payload):
        response = client.post("/books/review/", headers=headers, json=payload)
        results.append(response.status_code)

    # Run both submissions concurrently
    thread1 = threading.Thread(target=submit_review, args=(headers1, review_payload1))
    thread2 = threading.Thread(target=submit_review, args=(headers2, review_payload2))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    # Both requests should succeed
    assert results.count(200) == 2

###############################################################################
#                          Database Integrity Tests                         #
###############################################################################

def test_database_rollback_on_failure(setup_test_data, db_session):
    """Ensure database rolls back properly when an error occurs during review creation."""
    token = create_test_access_token(setup_test_data["users"][0])
    headers = {"Authorization": f"Bearer {token}"}

    # Simulating a failed request (invalid book title format)
    response = client.post("/books/review/", headers=headers, json={"book_title": "", "book_author": "", "review_text": "Invalid review"})
    assert response.status_code == 400

    # Ensure that no changes were made in the database
    review_count = db_session.query(Review).count()
    assert review_count == len(setup_test_data["reviews"])  # No new reviews added

