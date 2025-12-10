"""
Calculation Schemas Module

This module defines the Pydantic schemas for validation and serialization of calculation data.
It includes schemas for:
- Base calculation data (common fields)
- Creating new calculations
- Updating existing calculations
- Returning calculation responses

The schemas use Pydantic's validation system to ensure data integrity and provide
clear error messages when validation fails.
"""

from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class CalculationType(str, Enum):
    """
    Enumeration of valid calculation types.
    
    Using an Enum provides type safety and ensures that only valid
    calculation types are accepted. The str base class ensures that
    the values are serialized as strings in JSON.
    
    Benefits of using Enum:
    - Type checking at compile time
    - Documentation of valid values
    - Prevents typos and invalid values
    - Self-documenting code
    """
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"

class CalculationBase(BaseModel):
    """
    Base schema for calculation data.
    
    This schema defines the common fields that all calculation operations share:
    - type: The type of calculation (addition, subtraction, etc.)
    - inputs: A list of numeric values to operate on
    
    It also implements validation rules to ensure data integrity.
    """
    type: CalculationType = Field(
        ...,  # The ... means this field is required
        description="Type of calculation (addition, subtraction, multiplication, division)",
        example="addition"
    )
    inputs: List[float] = Field(
        ...,  # The ... means this field is required
        description="List of numeric inputs for the calculation",
        example=[10.5, 3, 2],
        min_items=2  # Ensures at least 2 numbers are provided
    )

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        """
        Validates the calculation type before conversion to an enum.
        
        This validator ensures that:
        1. The input is a string
        2. The value is one of the allowed calculation types
        3. The value is consistently converted to lowercase
        
        Args:
            v: The input value to validate
            
        Returns:
            str: The validated and normalized string value
            
        Raises:
            ValueError: If the input is not a valid calculation type
        """
        allowed = {e.value for e in CalculationType}
        # Ensure v is a string and check (in lowercase) if it's allowed.
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed))}")
        return v.lower()

    @field_validator("inputs", mode="before")
    @classmethod
    def check_inputs_is_list(cls, v):
        """
        Validates that the inputs field is a list.
        
        This validator runs before type conversion, ensuring that
        the input is actually a list before attempting to convert
        each element to float.
        
        Args:
            v: The input value to validate
            
        Returns:
            list: The validated list
            
        Raises:
            ValueError: If the input is not a list
        """
        if not isinstance(v, list):
            raise ValueError("Input should be a valid list")
        return v

    @model_validator(mode='after')
    def validate_inputs(self) -> "CalculationBase":
        """
        Validates the inputs based on calculation type.
        
        This validator runs after the model is created and performs
        business logic validation:
        1. Ensures there are at least 2 numbers for any calculation
        2. For division, ensures that no divisor is zero
        
        Returns:
            CalculationBase: The validated model
            
        Raises:
            ValueError: If validation fails
        """
        if len(self.inputs) < 2:
            raise ValueError("At least two numbers are required for calculation")
        if self.type == CalculationType.DIVISION:
            # Prevent division by zero (skip the first value as numerator)
            if any(x == 0 for x in self.inputs[1:]):
                raise ValueError("Cannot divide by zero")
        return self

    model_config = ConfigDict(
        # Allow conversion from SQLAlchemy models to Pydantic models
        from_attributes=True,
        
        # Add examples to the OpenAPI schema for better API documentation
        json_schema_extra={
            "examples": [
                {"type": "addition", "inputs": [10.5, 3, 2]},
                {"type": "division", "inputs": [100, 2]}
            ]
        }
    )

class CalculationCreate(CalculationBase):
    """
    Schema for creating a new Calculation.
    
    This extends the base schema with a user_id field for database insertion.
    In the API, this schema is not directly exposed to clients; instead, 
    the user_id is obtained from the authentication token.
    """
    user_id: UUID = Field(
        ...,
        description="UUID of the user who owns this calculation",
        example="123e4567-e89b-12d3-a456-426614174000"
    )

    model_config = ConfigDict(
        # Example for documentation and testing
        json_schema_extra={
            "example": {
                "type": "addition",
                "inputs": [10.5, 3, 2],
                "user_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )

class CalculationUpdate(BaseModel):
    """
    Schema for updating an existing Calculation.
    
    This schema is more restrictive than the create schema, as it only allows
    updating the inputs. The calculation type cannot be changed once created.
    
    Note that all fields are optional (so clients can send partial updates),
    but if inputs are provided, they must pass validation.
    """
    inputs: Optional[List[float]] = Field(
        None,  # None means this field is optional
        description="Updated list of numeric inputs for the calculation",
        example=[42, 7],
        min_items=2  # If provided, at least 2 items are required
    )

    @model_validator(mode='after')
    def validate_inputs(self) -> "CalculationUpdate":
        """
        Validates the inputs if they are being updated.
        
        This validator only runs if inputs are provided in the update request.
        It ensures that:
        - At least two numbers are provided for the calculation
        
        Note: Division-by-zero validation is handled at the model level
        when the result is calculated.
        
        Returns:
            CalculationUpdate: The validated model
            
        Raises:
            ValueError: If validation fails
        """
        if self.inputs is not None and len(self.inputs) < 2:
            raise ValueError("At least two numbers are required for calculation")
        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"inputs": [42, 7]}}
    )

class CalculationResponse(CalculationBase):
    """
    Schema for reading a Calculation from the database.
    
    This schema extends the base schema to include all fields that are
    returned when retrieving a calculation, including:
    - Database identifiers (id, user_id)
    - Timestamps (created_at, updated_at)
    - Computed result
    
    This schema is used for:
    - GET /calculations/{id} (single calculation)
    - GET /calculations (list of calculations)
    - POST /calculations (creation response)
    - PUT /calculations/{id} (update response)
    """
    id: UUID = Field(
        ...,
        description="Unique UUID of the calculation",
        example="123e4567-e89b-12d3-a456-426614174999"
    )
    user_id: UUID = Field(
        ...,
        description="UUID of the user who owns this calculation",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    created_at: datetime = Field(
        ..., 
        description="Time when the calculation was created"
    )
    updated_at: datetime = Field(
        ..., 
        description="Time when the calculation was last updated"
    )
    result: float = Field(
        ...,
        description="Result of the calculation",
        example=15.5
    )

    model_config = ConfigDict(
        # Allow conversion from SQLAlchemy models to this Pydantic model
        from_attributes=True,
        
        # Add a complete example for API documentation
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174999",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "type": "addition",
                "inputs": [10.5, 3, 2],
                "result": 15.5,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            }
        }
    )
