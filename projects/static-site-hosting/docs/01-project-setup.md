# Module 1: Project Setup

## Introduction

In this module, we'll set up the foundation for our FastAPI calculator application. We'll create the project structure, configure the environment, and set up our first FastAPI application.

## Objectives

- Create a proper project structure following best practices
- Set up a Python virtual environment
- Install necessary dependencies
- Configure FastAPI
- Create a basic "Hello World" endpoint

## Project Structure

A well-organized project structure helps maintain code quality and makes the application easier to extend. Here's the structure we'll create:

```
calculator-app/
│
├── app/                  # Main application package
│   ├── __init__.py      # Makes app a Python package
│   ├── auth/            # Authentication related code
│   ├── core/            # Core configuration and utilities
│   ├── models/          # Database models
│   ├── operations/      # Business logic
│   ├── schemas/         # Pydantic models for request/response
│   ├── database.py      # Database connection handling
│   └── main.py          # Application entry point
│
├── static/              # Static files (CSS, JS)
│
├── templates/           # HTML templates
│
├── tests/               # Test directory
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
│
├── .env                 # Environment variables (not in version control)
├── .gitignore           # Git ignore file
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile           # Docker configuration
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Setting Up the Environment

### 1. Create a virtual environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn[standard] sqlalchemy pydantic python-jose[cryptography] passlib[bcrypt] python-multipart jinja2 psycopg2-binary pytest alembic
pip freeze > requirements.txt
```

## Creating Our First FastAPI Application

Let's create a minimal FastAPI application in `app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(
    title="Calculations API",
    description="API for managing calculations",
    version="1.0.0"
)

@app.get("/health")
def read_health():
    """Health check endpoint."""
    return {"status": "ok"}
```

## Running the Application

Now we can run our application using Uvicorn:

```bash
uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000/health to see the response from our health check endpoint.

Also, check out the automatic API documentation at:
- http://127.0.0.1:8000/docs (Swagger UI)
- http://127.0.0.1:8000/redoc (ReDoc)

## Configuration Management

Create a configuration module in `app/core/config.py`:

```python
import os
from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/calculator"
    
    # JWT settings
    JWT_SECRET_KEY: str = "your-secret-key"  # Change in production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get application settings from environment variables or .env file."""
    return Settings()
```

## Next Steps

In the next module, we'll set up the database connection and create our first database models for users and calculations.

## Best Practices Covered

- Structured project organization
- Environment isolation with virtual environments
- Configuration management with Pydantic
- Documentation with docstrings and OpenAPI
- Health check endpoint for monitoring