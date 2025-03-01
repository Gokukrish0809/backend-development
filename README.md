## Book Review API
This is an Book review API that allows users to add reviews of books, edit their reviews, view reviews of books, and look up trending books. The API is built using **FastAPI**. 

## Features  

- **Security**: Register & log in using JWT authentication. 
- **Review Management**: Add or edit book reviews, which are automatically analyzed for sentiment (Positive, Neutral, Negative).
- **Retrieve reviews**: Retrieve reviews for a specific book by providing the book id. 
- **View books**: View reviews of all the books with optional sorting.
- **Get trending books**: See trending books, based on recent high positive review activity.  
- **Database Migrations**: Uses Alembic for schema migrations.  
- **Comprehensive Tests**: Includes unit and integration tests with `pytest`.

## Installation and setup

1. **Clone the repository**

2. **Setup a virtual environment:**
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install Dependencies:**
    pip install -r requirements.txt

4. **Set up the database:**
    alembic upgrade head

5. **Run the FastAPI server:**
    uvicorn main:app --reload

6. **Access API documentation:** (Swagger UI)
    http://127.0.0.1:8000/docs

7. **Running the test:**
    pytest



