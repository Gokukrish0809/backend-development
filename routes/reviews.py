"""
Book review System API Module

This module provides various operations such as registering an user account, 
logging in, creating a review, view the reviews of all the books in the system, 
get the reviews of one specific book, and get the trending books by count. 

Dependencies:
- FastAPI for API routing
- SQLAlchemy for database interactions
- Pydantic for request validation
- Logging for error handling and debugging
- Security utilities for authentication and role-based access control
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from models.models import Review, User, Book
from schemas.schemas import ReviewCreate, ReviewResponse, ReviewUpdate, BookResponse, BookWithReviewsResponse, ReviewResponseGrouped
from app.security import get_current_user
from ml.sentiment_analysis import analyze_sentiment
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import case

router = APIRouter(
    prefix = "/books",
    tags = ["Books"]
)

@router.get(
    "/", 
    response_model=List[BookWithReviewsResponse],
    summary = "Retrieve the reviews of all the books in the system",
    description = """Allows the users (no login required) to view the reviews of all the books in the system.
    The user can optionally sort by the number of positive or negative reviews.
    
    -**Default sorting**: Group the reviews by books and sort by the number of postive reviews.""",
    responses = {
        200: {
            "description": "Successful response with a list of reviews grouped by books.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "book_id": 101,
                            "book_title": "A sample book title",
                            "book_author": "A sample author",
                            "reviews": [
                                {
                                    "id": 1,
                                    "user_id": 11,
                                    "review_text": "Sample review",
                                    "sentiment": "positive/negative/neutral",
                                    "created_at": "2024-02-19T14:25:36.123456"

                                }
                            ]
                        }
                    ]
                }
            }
        },
        404: {"description": "No reviews found in the system"}
    })
def get_reviews(
    sort_by: str = None, 
    db: Session = Depends(get_db)):
    """Retrieve all reviews."""
    
    query = db.query(
        Review.id, Review.user_id, Review.book_id, Review.review_text, Review.sentiment, Review.created_at, 
        Book.title.label("book_title"), Book.author.label("book_author")
    ).join(Book, Book.id == Review.book_id)

    query = query.order_by(
        case(
            (Review.sentiment == "positive", 1),
            (Review.sentiment == "negative", 2),
            else_=3
        ),
        Review.created_at.desc()
    )

    reviews = query.all()

    if not reviews:
        raise HTTPException(status_code = 404, detail = "No reviews found in the system")

    # Group by book_id
    book_reviews = defaultdict(list)
    book_details = {}

    for row in reviews:
        book_details[row.book_id] = {"title": row.book_title, "author": row.book_author}
        book_reviews[row.book_id].append(
            ReviewResponseGrouped(
                id=row.id,
                user_id=row.user_id,
                review_text=row.review_text,
                sentiment=row.sentiment,
                created_at=row.created_at
            )
        )

    # Convert to structured response
    grouped_reviews = [
        {
            "book_id": book_id,
            "book_title": book_details[book_id]["title"],
            "book_author": book_details[book_id]["author"],
            "reviews": book_reviews[book_id]
        }
        for book_id in book_reviews
    ]

    return grouped_reviews

@router.get(
    "/review/{book_id}", 
    response_model = List[ReviewResponseGrouped],
    summary = "Retrieve the reviews of one specific book in the system",
    description = "Allows the users (no login required) to view the reviews of one specific book in the system.",
    responses = {
        200: {
            "description": "Successful response with a list of reviews of the book.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            
                            "id": 1,
                            "user_id": 11,
                            "review_text": "Sample review",
                            "sentiment": "positive/negative/neutral",
                            "created_at": "2024-02-19T14:25:36.123456"                               
                        }
                    ]
                }
            }
        },
        404: {"description": "No reviews found for this book"}
    })
def get_reviews_by_book(book_id: int, db: Session = Depends(get_db)):
    """Retrieve all reviews of a book."""
    reviews = db.query(Review).filter(Review.book_id == book_id).all()

    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this book")
    
    return [
        {
            "id": review.id,
            "user_id": review.user_id,  
            "review_text": review.review_text,
            "sentiment": review.sentiment,
            "created_at": review.created_at
        }
        for review in reviews
    ]

@router.get(
    "/trending/{count}", 
    response_model = List[BookResponse],
    summary = "Retrieve the trending books in the review system",
    description = """Allows the users (no login required) to view the current trending books by count in the system.
    If the count is not specified, the current 10 trending books will be returned""",
    responses = {
        200: {
            "description": (
                "Successful response with a list of current trending books in the system. "
                "If no trending books are available, an empty list will be returned."
            ),
            "content": {
                "application/json": {
                    "example": [
                        {
                            
                            "id": 1,
                            "user_id": 11,
                            "review_text": "Sample review",
                            "sentiment": "positive/negative/neutral",
                            "created_at": "2024-02-19T14:25:36.123456"                               
                        }
                    ]
                }
            }
        },
        404: {"description": "No books in the system"},
    })
def get_trending_books(count: int = 10, db: Session = Depends(get_db)):
    """Retrieve the current trending books."""
    one_week_ago = datetime.utcnow() - timedelta(weeks=1)
    recent_reviews = db.query(Review.book_id).filter(
        Review.created_at >= one_week_ago,
        Review.sentiment == "positive"
    ).subquery()

    books = db.query(Book).filter(Book.id.in_(recent_reviews)).all()
    book_positive_counts = {}

    if not books:
        raise HTTPException(status_code = 404, detail = "No books in the system")

    for book in books:
        positive_count = sum(
            1 for review in book.reviews
            if review.sentiment == "positive" and review.created_at >= one_week_ago
        )

        if positive_count > 0:
            book_positive_counts[book] = positive_count

    if not book_positive_counts:
        return []

    trending_books = sorted(book_positive_counts.keys(), key = lambda b: book_positive_counts[b], reverse = True)

    return [
        BookResponse(
            id=book.id,
            title=book.title,
            author=book.author,
            review_count=book_positive_counts[book]
        )
        for book in trending_books[:count]
    ]

@router.post(
    "/review/", 
    response_model = ReviewResponse,
    summary = "Create a new review for a book",
    description = """Allows the users to create a new review for a book.
    
    **Authentication Required**  
      - This endpoint requires a valid JWT token.""",
    responses = {
        200: {
            "description": "Successful response with the details of the created review.",
            "content": {
                "application/json": {
                    "example": {
                            "id": 1,
                            "user_id": 11,
                            "book_id": 101,
                            "book_title": "Sample book title",
                            "book_author": "Sample book author",
                            "review_text": "Sample review",
                            "sentiment": "positive/negative/neutral",
                            "created_at": "2024-02-19T14:25:36.123456"                               
                    }
                }
            }
        },
        401: {"description": "Invalid or missing authentication token."},
        404: {"description": "Book 'sample book title' by 'sample book author' not found"},
        400: {"description": "Review text exceeds the character limit or the user has already reviewed the book"}
    })
def create_review(review_data: ReviewCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    if any(x in review_data.review_text.lower() for x in ["'); drop table", "delete from", "--"]) or len(review_data.book_title) == 0 or len(review_data.book_author) == 0:
        raise HTTPException(status_code=400, detail="Invalid input detected.")

    if len(review_data.review_text) > 1000:
        raise HTTPException(status_code=400, detail="Review text exceeds 5000 characters")

    book = db.query(Book).filter(
        Book.title == review_data.book_title,
        Book.author == review_data.book_author
    ).first()

    if not book:
        raise HTTPException(status_code=404, detail=f"Book not found")

    existing_review = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.book_id == book.id
    ).first()

    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this book.")

    predicted_sentiment = analyze_sentiment(review_data.review_text)

    new_review = Review(
        user_id = current_user.id,
        book_id = book.id,
        review_text = review_data.review_text,
        sentiment = predicted_sentiment,
        created_at=datetime.utcnow()
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return ReviewResponse(
        id = new_review.id,
        user_id = new_review.user_id,
        book_id = book.id,
        book_title = review_data.book_title,
        book_author = review_data.book_author,
        review_text = new_review.review_text,
        sentiment = new_review.sentiment,
        created_at = new_review.created_at    
    )

@router.put(
    "/review/", 
    response_model = ReviewResponse,
    summary = "Update the existing review of a book",
    description = """Allows the users to update a review they created for a book.
    
    **Authentication Required**  
        - This endpoint requires a valid JWT token.
    **Raises**
        - 404 NOT FOUND: If the review with the given ID does not exist.
        - 404 NOT FOUND: If the book with the given title and author does not exist.""",
    responses = {
        200: {
            "description": "Successful response with the details of the updated review.",
            "content": {
                "application/json": {
                    "example": {
                            "id": 1,
                            "user_id": 11,
                            "book_id": 101,
                            "book_title": "Sample book title",
                            "book_author": "Sample book author",
                            "review_text": "Sample review",
                            "sentiment": "positive/negative/neutral",
                            "created_at": "2024-02-19T14:25:36.123456"                               
                    }
                }
            }
        },
        401: {"description": "Invalid or missing authentication token."},
        404: {"description": "Review or book not found"}
    })
def update_review(review_data: ReviewUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    
    if any(x in review_data.lower() for x in ["drop table", "delete from", "--"]):
        raise HTTPException(status_code=400, detail="Invalid input detected.")
    
    review = db.query(Review).filter(
        Review.id == review_data.id
    ).first()

    if not review:
        raise HTTPException(status_code = 404, detail = "Review not found")

    book = db.query(Book).filter(
        Book.title == review_data.book_title,
        Book.author == review_data.book_author
    ).first()

    if not book:
        raise HTTPException(status_code = 404, detail = "Book not found")

    review.book_id = book.id
    review.review_text = review_data.review_text
    review.sentiment = analyze_sentiment(review_data.review_text)

    db.commit()
    db.refresh(review)

    return ReviewResponse(
        id = review_data.id,
        user_id = review.user_id,
        book_id = book.id,
        book_title = review_data.book_title,
        book_author = review_data.book_author,
        review_text = review_data.review_text,
        sentiment = review.sentiment,
        created_at = review.created_at    
    )
