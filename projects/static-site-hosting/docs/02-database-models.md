# Module 2: Database Models

## Introduction

In this module, we'll set up the database connection and define our database models. We'll use SQLAlchemy, a powerful Object-Relational Mapping (ORM) library for Python, to interact with the database.

## Objectives

- Set up database connection with SQLAlchemy
- Understand database models and ORM concepts
- Create the User model
- Create the Calculation model with polymorphic inheritance
- Understand model relationships

## Setting Up the Database Connection

First, let's create a database connection module in `app/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Dependency function that creates a new SQLAlchemy session for each request.
    The session is automatically closed when the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

This module:
1. Creates a database engine using the URL from our settings
2. Creates a SessionLocal class for database sessions
3. Creates a Base class for our models to inherit from
4. Provides a dependency function for getting a database session

## Creating the User Model

Now, let's create the User model in `app/models/user.py`:

```python
# app/models/user.py

import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, String, Boolean, DateTime, or_
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from app.core.config import get_settings
from app.database import Base

settings = get_settings()

def utcnow():
    """Helper function to get current UTC datetime"""
    return datetime.now(timezone.utc)

class User(Base):
    """User model with authentication and token management capabilities."""
    
    __tablename__ = "users"
    
    # Primary key and identifying fields
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    
    # Personal information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    
    # Status flags
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    calculations = relationship("Calculation", back_populates="user", cascade="all, delete-orphan")
```

## Creating the Calculation Model with Polymorphic Inheritance

For our calculation model, we'll use SQLAlchemy's polymorphic inheritance to create different types of calculations:

```python
# app/models/calculation.py
from datetime import datetime
import uuid
from typing import List
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.ext.declarative import declared_attr
from app.database import Base

class AbstractCalculation:
    """Abstract base class for calculations"""
    
    @declared_attr
    def __tablename__(cls):
        return 'calculations'

    @declared_attr
    def id(cls):
        return Column(
            UUID(as_uuid=True), 
            primary_key=True, 
            default=uuid.uuid4,
            nullable=False
        )

    @declared_attr
    def user_id(cls):
        return Column(
            UUID(as_uuid=True), 
            ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        )

    @declared_attr
    def type(cls):
        return Column(
            String(50), 
            nullable=False,
            index=True
        )

    @declared_attr
    def inputs(cls):
        return Column(
            JSON, 
            nullable=False
        )

    @declared_attr
    def result(cls):
        return Column(
            Float,
            nullable=True
        )

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime, 
            default=datetime.utcnow,
            nullable=False
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime, 
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )

    @declared_attr
    def user(cls):
        return relationship("User", back_populates="calculations")

    @classmethod
    def create(cls, calculation_type: str, user_id: uuid.UUID, inputs: List[float]) -> "Calculation":
        """Factory method to create calculations"""
        calculation_classes = {
            'addition': Addition,
            'subtraction': Subtraction,
            'multiplication': Multiplication,
            'division': Division,
        }
        calculation_class = calculation_classes.get(calculation_type.lower())
        if not calculation_class:
            raise ValueError(f"Unsupported calculation type: {calculation_type}")
        return calculation_class(user_id=user_id, inputs=inputs)

    def get_result(self) -> float:
        """Method to compute calculation result"""
        raise NotImplementedError

class Calculation(Base, AbstractCalculation):
    """Base calculation model"""
    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "calculation",
    }

class Addition(Calculation):
    """Addition calculation"""
    __mapper_args__ = {"polymorphic_identity": "addition"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        return sum(self.inputs)

class Subtraction(Calculation):
    """Subtraction calculation"""
    __mapper_args__ = {"polymorphic_identity": "subtraction"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = self.inputs[0]
        for value in self.inputs[1:]:
            result -= value
        return result

class Multiplication(Calculation):
    """Multiplication calculation"""
    __mapper_args__ = {"polymorphic_identity": "multiplication"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = 1
        for value in self.inputs:
            result *= value
        return result

class Division(Calculation):
    """Division calculation"""
    __mapper_args__ = {"polymorphic_identity": "division"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("Inputs must be a list with at least two numbers.")
        result = self.inputs[0]
        for value in self.inputs[1:]:
            if value == 0:
                raise ValueError("Cannot divide by zero.")
            result /= value
        return result
```

## Understanding Polymorphic Inheritance

The Calculation model uses SQLAlchemy's polymorphic inheritance, which allows:

1. **Single Table Inheritance**: All calculation types are stored in a single database table
2. **Type Discrimination**: The `type` column identifies which calculation subclass to use
3. **Specialized Behavior**: Each calculation subclass implements its own `get_result()` method
4. **Factory Pattern**: The `create()` class method provides a factory pattern for creating the right calculation type

## Model Relationships

Notice the relationship between User and Calculation:

1. A user has many calculations (`User.calculations`)
2. A calculation belongs to a user (`Calculation.user`)
3. When a user is deleted, all their calculations are also deleted (`cascade="all, delete-orphan"`)

## Creating Database Tables

To create database tables, we'll update our `app/main.py` file to create tables on startup:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    yield

app = FastAPI(
    title="Calculations API",
    description="API for managing calculations",
    version="1.0.0",
    lifespan=lifespan
)
```

## Next Steps

In the next module, we'll create Pydantic schemas for request and response validation, and build our API endpoints.

## Best Practices Covered

- Using SQLAlchemy ORM for database interaction
- Single Table Inheritance with polymorphic models
- Factory pattern for object creation
- Proper relationship modeling
- Automatic table creation on application startup