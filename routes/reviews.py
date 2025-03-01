from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from models.models import Review, User, Book
from schemas.schemas import ReviewCreate, ReviewResponse, ReviewUpdate, BookResponse, BookWithReviewsResponse
from app.security import get_current_user
from ml.sentiment_analysis import analyze_sentiment
from datetime import datetime, timedelta
from collections import defaultdict

router = APIRouter(
    prefix = "/books",
    tags = ["Books"]
)

@router.get("/", response_model=List[BookWithReviewsResponse])
def get_reviews(sort_by: str = None, db: Session = Depends(get_db)):
    """Retrieve all reviews."""
    query = db.query(
        Review.id, Review.user_id, Review.book_id, Review.review_text, Review.sentiment, Review.created_at, 
        Book.title.label("book_title"), Book.author.label("book_author")
    ).join(Book, Book.id == Review.book_id)

    if sort_by == "positive" or sort_by == None:
        query = query.order_by(Review.sentiment == "positive", Review.created_at.desc())
    elif sort_by == "negative":
        query = query.order_by(Review.sentiment == "negative", Review.created_at.desc())

    reviews = query.all()

    # Group by book_id
    book_reviews = defaultdict(list)
    book_details = {}

    for row in reviews:
        book_details[row.book_id] = {"title": row.book_title, "author": row.book_author}
        book_reviews[row.book_id].append(
            ReviewResponse(
                id=row.id,
                user_id=row.user_id,
                book_id=row.book_id,
                book_title=row.book_title,
                book_author=row.book_author,
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

@router.get("/review/{book_id}", response_model = List[ReviewResponse])
def get_reviews(book_id: int, db: Session = Depends(get_db)):
    """Retrieve all reviews of a book."""
    reviews = db.query(Review).filter(Review.book_id == book_id).all()

    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this book")
    
    return [
        ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            book_id=review.book_id,
            book_title=review.book.title,  
            book_author=review.book.author,  
            review_text=review.review_text,
            sentiment=review.sentiment,
            created_at=review.created_at
        )
        for review in reviews
    ]

@router.get("/trending/{count}", response_model = List[BookResponse])
def get_trending_books(count: int, db: Session = Depends(get_db)):
    one_week_ago = datetime.utcnow() - timedelta(weeks=1)
    books = db.query(Book).options(joinedload(Book.reviews)).all()
    book_positive_counts = {}

    for book in books:
        positive_count = sum(
            1 for review in book.reviews
            if review.sentiment == "positive" and review.created_at >= one_week_ago
        )

        if positive_count > 0:
            book_positive_counts[book] = positive_count

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

@router.post("/review", response_model = ReviewResponse)
def create_review(review_data: ReviewCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    book = db.query(Book).filter(
        Book.title == review_data.book_title,
        Book.author == review_data.book_author
    ).first()

    if not book:
        raise HTTPException(status_code=404, detail=f"Book '{review_data.book_title}' by {review_data.book_author} not found")

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

@router.put("/review", response_model = ReviewResponse)
def update_review(review_data: ReviewUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    review = db.query(Review).filter(
        Review.id == review_data.id
    ).first()

    if not review:
        raise HTTPException(status_code = 404, detail = "Review does not exist")

    book = db.query(Book).filter(
        Book.title == review_data.book_title,
        Book.author == review_data.book_author
    ).first()

    if not book:
        raise HTTPException(status_code = 404, detail = "Book not found")

    review.book_id = book.id
    review.review_text = review_data.review_text
    review.sentiment = analyze_sentiment(review_data.review_text)
    review.created_at = datetime.utcnow()

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
