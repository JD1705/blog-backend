# Blog Backend API

This project is a robust and modern backend API for a blog platform, built with FastAPI. It provides core functionalities for managing users, posts, and comments, featuring a well-structured architecture, secure authentication, and efficient data handling with MongoDB.

## Features

*   **RESTful API**: Exposes a clean and intuitive API for all blog operations.
*   **User Management**: Supports user registration, authentication, and role-based access control.
*   **Post Management**: Allows creating, reading, updating, and deleting blog posts with features like tags, slugs, and rich content.
*   **Comment System**: Enables users to comment on posts.
*   **JWT Authentication**: Secure user authentication and authorization using JSON Web Tokens.
*   **MongoDB Integration**: Utilizes MongoDB for flexible and scalable data storage.
*   **Pydantic for Data Validation**: Ensures data integrity and type safety across the API.
*   **Automatic Database Indexing**: Models define their own indexes, which are automatically created on application startup for optimized query performance.
*   **Slug Generation**: Automatic and unique slug generation for posts to ensure SEO-friendly URLs.
*   **Modular Architecture**: Clear separation of concerns with dedicated modules for API routes, services, models, and schemas.

## Technologies Used

*   **FastAPI**: High-performance web framework for building APIs with Python 3.7+.
*   **Pydantic**: Data validation and settings management using Python type hints.
*   **MongoDB**: NoSQL database for flexible data storage.
*   **PyMongo**: Official MongoDB driver for Python.
*   **python-jose**: JWT (JSON Web Token) implementation in Python.
*   **passlib**: Cryptographic hashing framework for password security.
*   **Uvicorn**: ASGI server for running FastAPI applications.

## Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

*   Python 3.8+
*   MongoDB instance (local or cloud-based)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/blog-backend-api.git
    cd blog-backend-api
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    Create a `.env` file in the project root based on `.env.example`.

    ```ini
    # .env
    MONGO_CONNECTION_STRING="mongodb://localhost:27017/blogdb"
    JWT_SECRET_KEY="your_super_secret_jwt_key" # Change this!
    JWT_ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

    *   `MONGO_CONNECTION_STRING`: Your MongoDB connection string.
    *   `JWT_SECRET_KEY`: A strong secret key for signing JWT tokens. **Generate a strong, random key for production.**
    *   `JWT_ALGORITHM`: The algorithm used for JWT signing (e.g., HS256).
    *   `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiration time for access tokens in minutes.

### Running the Application

1.  **Start the FastAPI server:**
    ```bash
    uvicorn src.main:app --reload
    ```
    The `--reload` flag enables auto-reloading of the server on code changes, which is useful for development.

2.  **Access the API documentation:**
    Once the server is running, you can access the interactive API documentation (Swagger UI) at:
    `http://localhost:8000/docs`

    Or the ReDoc documentation at:
    `http://localhost:8000/redoc`

## Project Structure

```
.
├── src/
│   ├── main.py                 # Main FastAPI application entry point
│   ├── api/                    # API routes (auth, users, posts, comments)
│   │   └── routes/
│   ├── core/                   # Core application components (config, database, security)
│   ├── models/                 # Pydantic models for database entities
│   ├── schemas/                # Pydantic schemas for request/response validation
│   └── services/               # Business logic and utility functions
├── tests/                      # Unit and integration tests
├── requirements.txt            # Project dependencies
├── .env.example                # Example environment variables
├── LICENSE                     # Project license
└── README.md                   # This README file
```

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.
