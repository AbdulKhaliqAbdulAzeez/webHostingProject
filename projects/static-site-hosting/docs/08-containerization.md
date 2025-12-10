# Module 8: Containerization with Docker

## Introduction

In this module, we'll containerize our FastAPI application using Docker. Containerization packages an application and its dependencies into a single unit called a container, making it easier to deploy and run consistently across different environments.

## Objectives

- Understand the benefits of containerization
- Create a Dockerfile for our FastAPI application
- Set up a Docker Compose configuration for development
- Learn how to build and run Docker containers
- Configure environment variables for different deployment environments

## Why Containerization?

Containerization offers several benefits:

1. **Consistency**: Ensures the application runs the same way in every environment
2. **Isolation**: Isolates the application and its dependencies from the host system
3. **Portability**: Allows the application to run on any system that supports Docker
4. **Scalability**: Makes it easier to scale the application horizontally
5. **Version Control**: Enables versioning of the entire application environment
6. **Dependency Management**: Simplifies managing dependencies and their versions

## Creating a Dockerfile

Let's create a Dockerfile for our FastAPI application:

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This Dockerfile:
1. Uses Python 3.10 slim image as the base
2. Sets up the working directory
3. Configures environment variables
4. Installs system dependencies
5. Installs Python dependencies
6. Copies the application code
7. Exposes the application port
8. Specifies the command to run the application

## Setting Up Docker Compose

Docker Compose allows us to define and run multi-container Docker applications. Let's create a `docker-compose.yml` file:

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/calculator
      - JWT_SECRET_KEY=your_secret_key_change_in_production
    depends_on:
      - db
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=calculator
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

This Docker Compose configuration:
1. Defines two services: `web` (our FastAPI app) and `db` (PostgreSQL database)
2. Maps ports from the container to the host
3. Mounts volumes for code and database data
4. Sets environment variables
5. Specifies dependencies between services
6. Configures commands to run

## Database Initialization

We need to initialize the database when the containers start. Let's create an initialization script:

```bash
#!/bin/bash
# init-db.sh

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL
```

And add it to our Docker Compose configuration:

```yaml
db:
  image: postgres:14
  volumes:
    - postgres_data:/var/lib/postgresql/data/
    - ./init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
  environment:
    - POSTGRES_USER=postgres
    - POSTGRES_PASSWORD=postgres
    - POSTGRES_DB=calculator
  ports:
    - "5432:5432"
```

## Environment Variables

For better configuration management, let's update our application to use environment variables:

```python
# app/core/config.py
import os
from pydantic import BaseSettings, PostgresDsn
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    # Default values for local development
    DATABASE_URL: PostgresDsn = "postgresql://postgres:postgres@localhost:5432/calculator"
    JWT_SECRET_KEY: str = "your_secret_key_change_in_production"
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

## Building and Running with Docker

To build and run the application with Docker:

```bash
# Build and start the containers
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop the containers
docker-compose down

# View logs
docker-compose logs -f

# Access the web container
docker-compose exec web bash
```

## Managing Database Migrations

For database migrations, we can use Alembic with Docker:

1. Add Alembic to our requirements:

```
alembic==1.7.7
```

2. Initialize Alembic:

```bash
docker-compose exec web alembic init migrations
```

3. Configure Alembic (`alembic.ini`):

```ini
# alembic.ini
sqlalchemy.url = postgresql://postgres:postgres@db:5432/calculator
```

4. Set up the migration environment (`migrations/env.py`):

```python
# migrations/env.py
from app.database import Base
from app.models.user import User
from app.models.calculation import Calculation

target_metadata = Base.metadata
```

5. Create and run migrations:

```bash
# Create a migration
docker-compose exec web alembic revision --autogenerate -m "Initial migration"

# Run migrations
docker-compose exec web alembic upgrade head
```

## Production Configuration

For production, we'd make several changes:

1. Use environment variables for secrets, not hardcoded values
2. Optimize the Dockerfile for production
3. Disable debug mode
4. Use a production-ready ASGI server like Gunicorn with Uvicorn workers
5. Add health checks
6. Implement proper logging

Here's an example production Dockerfile:

```dockerfile
# Dockerfile.prod
FROM python:3.10-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder stage
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run using Gunicorn with Uvicorn workers
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## Docker Best Practices

1. **Use multi-stage builds**: Reduces image size by separating build and runtime environments
2. **Minimize layers**: Combine related commands to reduce the number of layers
3. **Use .dockerignore**: Exclude files not needed in the container
4. **Don't run as root**: Use a non-root user for security
5. **Pin dependencies**: Specify exact versions for reproducibility
6. **Optimize caching**: Order Dockerfile commands to maximize cache efficiency
7. **Health checks**: Add health checks to monitor container health
8. **Logging**: Configure proper logging for observability

## Creating a .dockerignore File

To exclude files from the Docker build context, create a `.dockerignore` file:

```
# .dockerignore
.git
.gitignore
.env
.venv
venv
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.tox/
.idea/
.vscode/
*.sublime-project
*.sublime-workspace
media/
```

## Next Steps

In the next module, we'll deploy our containerized application to a cloud provider.

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)