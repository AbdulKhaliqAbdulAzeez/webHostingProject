# app/schemas/token.py
from enum import Enum
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class TokenType(str, Enum):
    """Valid token types."""
    ACCESS = "access"
    REFRESH = "refresh"

class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_at": "2025-01-01T00:00:00"
            }
        }
    )

class TokenData(BaseModel):
    """Schema for JWT token payload."""
    user_id: UUID = Field(..., description="User ID from the token")
    exp: datetime = Field(..., description="Token expiration timestamp")
    jti: str = Field(..., description="Unique token identifier")
    token_type: TokenType = Field(..., description="Type of token")

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    """Schema for complete token response including user data."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    user_id: UUID = Field(..., description="User's UUID")
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    is_active: bool = Field(..., description="User's active status")
    is_verified: bool = Field(..., description="User's verification status")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_at": "2025-01-01T00:00:00",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "is_verified": False
            }
        }
    )
