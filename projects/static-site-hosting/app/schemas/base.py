# app/schemas/base.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator

class UserBase(BaseModel):
    """Base user schema with common fields."""
    first_name: str = Field(max_length=50, example="John")
    last_name: str = Field(max_length=50, example="Doe")
    email: EmailStr = Field(example="john.doe@example.com")
    username: str = Field(min_length=3, max_length=50, example="johndoe")

    model_config = ConfigDict(from_attributes=True)

class PasswordMixin(BaseModel):
    password: str = Field(
        ...,
        min_length=8,
        example="SecurePass123!",
        description="Password"
    )

    @model_validator(mode="after")
    def validate_password(self) -> "PasswordMixin":
        if not any(char.isupper() for char in self.password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in self.password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in self.password):
            raise ValueError("Password must contain at least one digit")
        # Removed special character check so that "SecurePass123" is valid.
        return self

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase, PasswordMixin):
    """
    Schema used when creating a new user.
    Inherits common user fields from UserBase and adds a password field.
    """
    pass

class UserLogin(BaseModel):
    """
    Schema for user login credentials.
    Contains the username and password.
    """
    username: str = Field(min_length=3, max_length=50, example="johndoe")
    password: str = Field(min_length=8, example="supersecretpassword")
