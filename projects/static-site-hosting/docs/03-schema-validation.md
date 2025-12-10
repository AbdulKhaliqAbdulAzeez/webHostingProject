# Module 3: Schema Validation with Pydantic

## Introduction

In this module, we'll learn about schema validation using Pydantic. Pydantic is a data validation and settings management library using Python type annotations. It ensures that the data received by our API endpoints and sent in responses is valid according to our specifications.

## Objectives

- Understand the importance of data validation
- Create Pydantic models for request and response validation
- Learn about schema inheritance and composition
- Implement validation for our API endpoints

## Why Data Validation Matters

Data validation is crucial in API development for several reasons:

1. **Security**: Preventing malicious input that could lead to security vulnerabilities
2. **Data Integrity**: Ensuring that the data stored in our database is valid and consistent
3. **Documentation**: Automatically generating API documentation through OpenAPI
4. **Type Safety**: Leveraging Python's type system for better code quality and IDE support
5. **Error Handling**: Providing meaningful error messages to clients when validation fails

## Creating Base Schema Models

Let's start by creating base schemas that will be shared across different schema types:

```python
# app/schemas/base.py
from datetime import datetime
from typing import Optional, TypeVar, Generic, List
from pydantic import BaseModel, Field

# Define a generic type for our models
T = TypeVar('T')

class BaseSchema(BaseModel):
    """Base schema with common configuration for all schemas."""
    
    class Config:
        """Pydantic config for all schemas."""
        # Allow conversion from ORM models to Pydantic models
        orm_mode = True
        # Validate all assignment even after model creation
        validate_assignment = True
        # Use the field name in the schema if an alias is not provided
        populate_by_name = True
        # Allow extra fields that aren't in the schema during validation
        # They will be discarded when converting to model
        extra = "ignore"
```

## Creating User Schemas

Now, let's create the schemas for user-related operations:

```python
# app/schemas/user.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, validator, root_validator

from app.schemas.base import BaseSchema

class UserBase(BaseSchema):
    """Base schema for user data."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

class UserCreate(UserBase):
    """Schema for creating a new user (registration)."""
    password: str = Field(..., min_length=6)
    confirm_password: str
    
    @root_validator
    def passwords_match(cls, values):
        """Validate that password and confirm_password match."""
        password = values.get('password')
        confirm_password = values.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValueError('Passwords do not match')
        return values

class UserLogin(BaseSchema):
    """Schema for user login."""
    username: str  # Can be username or email
    password: str

class UserResponse(UserBase):
    """Schema for user data in responses."""
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
```

## Creating Calculation Schemas

Next, let's create schemas for our calculation operations:

```python
# app/schemas/calculation.py
from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator

from app.schemas.base import BaseSchema

class CalculationBase(BaseSchema):
    """Base schema for calculation data."""
    type: str = Field(..., description="Type of calculation: addition, subtraction, multiplication, division")
    inputs: List[float] = Field(..., min_items=2, description="List of input numbers")
    
    @validator('type')
    def validate_calculation_type(cls, v):
        """Validate the calculation type."""
        valid_types = ['addition', 'subtraction', 'multiplication', 'division']
        if v.lower() not in valid_types:
            raise ValueError(f'Type must be one of: {", ".join(valid_types)}')
        return v.lower()

class CalculationResponse(CalculationBase):
    """Schema for calculation data in responses."""
    id: UUID
    user_id: UUID
    result: float
    created_at: datetime
    updated_at: datetime

class CalculationUpdate(BaseSchema):
    """Schema for updating an existing calculation."""
    inputs: Optional[List[float]] = Field(None, min_items=2, description="List of input numbers")
```

## Creating Token Schemas

For authentication, we'll need token schemas:

```python
# app/schemas/token.py
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.schemas.base import BaseSchema

class TokenType(str, Enum):
    """Enum for token types."""
    ACCESS = "access"
    REFRESH = "refresh"

class TokenResponse(BaseSchema):
    """Schema for token response after successful login."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_at: datetime
    
    # User information included in the token response
    user_id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
```

## Using Schemas in API Endpoints

Now that we have our schemas defined, we can use them in our API endpoints to validate requests and responses:

```python
@app.post(
    "/auth/register", 
    response_model=UserResponse,  # Validates the response
    status_code=status.HTTP_201_CREATED,
    tags=["auth"]
)
def register(
    user_create: UserCreate,  # Validates the request body
    db: Session = Depends(get_db)
):
    """Create a new user account."""
    user_data = user_create.dict(exclude={"confirm_password"})
    try:
        user = User.register(db, user_data)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
```

## Benefits of Using Pydantic

1. **Automatic Validation**: Pydantic automatically validates request data
2. **Meaningful Error Messages**: Clear error messages when validation fails
3. **Documentation**: Generates OpenAPI schema for API documentation
4. **Type Hints**: Provides type information to your IDE
5. **Conversion**: Handles conversion between types (e.g., string to datetime)

## Best Practices

1. **Separate Schemas**: Create different schemas for different operations (create, update, response)
2. **Schema Inheritance**: Use inheritance to avoid duplicating code
3. **Validation Methods**: Use Pydantic validators for complex validation logic
4. **Documentation**: Add field descriptions for better API documentation
5. **Config Options**: Use Pydantic Config for fine-grained control

## Next Steps

In the next module, we'll implement the authentication system using JWT tokens and implement security best practices.

## Additional Resources

- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [FastAPI Schema Documentation](https://fastapi.tiangolo.com/tutorial/schema/)
- [Pydantic Field Types](https://pydantic-docs.helpmanual.io/usage/types/)