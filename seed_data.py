from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.security import get_password_hash
from models.models import User, Book, Review
from ml.sentiment_analysis import analyze_sentiment

# Create a new session
db: Session = SessionLocal()

# Clear existing data (Optional: Uncomment if you want to wipe before seeding)
db.query(Review).delete()
db.query(Book).delete()
db.query(User).delete()
db.commit()

# Sample users
users = [
    {"username": "alice", "email": "alice@example.com", "password": "password123"},
    {"username": "bob", "email": "bob@example.com", "password": "securepass"},
]

# Sample books
books = [
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"title": "1984", "author": "George Orwell"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
]

# Seed Users
user_objects = []
for user in users:
    hashed_password = get_password_hash(user["password"])
    user_obj = User(username=user["username"], email=user["email"], password_hash=hashed_password)
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    user_objects.append(user_obj)

# Seed Books
book_objects = []
for book in books:
    book_obj = Book(title=book["title"], author=book["author"])
    db.add(book_obj)
    db.commit()
    db.refresh(book_obj)
    book_objects.append(book_obj)

# Sample reviews
reviews = [
    {"user": user_objects[0], "book": book_objects[0], "text": "An amazing book! A must-read."},
    {"user": user_objects[1], "book": book_objects[1], "text": "This book changed my perspective on society."},
    {"user": user_objects[0], "book": book_objects[2], "text": "I found it quite dull and overrated."},
]

# Seed Reviews
for review in reviews:
    sentiment = analyze_sentiment(review["text"])
    review_obj = Review(
        user_id=review["user"].id,
        book_id=review["book"].id,
        review_text=review["text"],
        sentiment=sentiment,
        created_at=datetime.utcnow() - timedelta(days=2),  # Simulating past reviews
    )
    db.add(review_obj)

# Commit all changes
db.commit()

print("✅ Database seeding completed successfully!")

# Close session
db.close()
