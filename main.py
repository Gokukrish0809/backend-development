"""
Main Application Entry Point

This module initializes the FastAPI application, sets up API routes, and 
ensures database models are properly linked.

Dependencies:
    - FastAPI for building the API
    - SQLAlchemy for database interactions
    - Application-specific modules (auth, accounts)
"""
from fastapi import FastAPI
from app.database import engine
from models import models
from routes import auth, reviews

# -----------------------------------
# FastAPI Application Initialization
# -----------------------------------
app = FastAPI(
    title="Book review API",
    description="A simple book review API for managing book reviews, analyzing the sentiment of the reviews, and view the trending books.",
    version="1.0.0"
)


# -----------------------------------
# Register API Routes
# -----------------------------------
app.include_router(auth.router)# Authentication-related routes
app.include_router(reviews.router) # Review management routes

# -----------------------------------
# Root Endpoint
# -----------------------------------
@app.get("/", tags=["General"])
def home():
    """Root endpoint that returns a welcome message."""
    return{"message": "Welcome to the Book review system"}