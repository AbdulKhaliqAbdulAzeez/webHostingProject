# Module 5: API Endpoints (BREAD Operations)

## Introduction

In this module, we'll implement the API endpoints for our calculator application. We'll follow the BREAD pattern, which stands for Browse, Read, Edit, Add, Delete. This is a variation of the more common CRUD (Create, Read, Update, Delete) pattern.

## Objectives

- Understand the BREAD pattern for API design
- Implement REST API endpoints for calculations
- Learn how to handle path and query parameters
- Implement error handling for API endpoints
- Secure endpoints with authentication

## The BREAD Pattern

The BREAD pattern is a variation of CRUD that is more user-centric:

- **Browse**: List or search for resources (GET /calculations)
- **Read**: Retrieve a specific resource (GET /calculations/{id})
- **Edit**: Update an existing resource (PUT /calculations/{id})
- **Add**: Create a new resource (POST /calculations)
- **Delete**: Remove a resource (DELETE /calculations/{id})

## Implementing Calculation Endpoints

Let's implement the BREAD operations for our calculations:

### Add (Create) Calculation

```python
@app.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["calculations"],
)
def create_calculation(
    calculation_data: CalculationBase,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new calculation for the authenticated user.
    Automatically computes the 'result'.
    """
    try:
        new_calculation = Calculation.create(
            calculation_type=calculation_data.type,
            user_id=current_user.id,
            inputs=calculation_data.inputs,
        )
        new_calculation.result = new_calculation.get_result()

        db.add(new_calculation)
        db.commit()
        db.refresh(new_calculation)
        return new_calculation

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

### Browse (List) Calculations

```python
@app.get("/calculations", response_model=List[CalculationResponse], tags=["calculations"])
def list_calculations(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all calculations belonging to the current authenticated user.
    """
    calculations = db.query(Calculation).filter(Calculation.user_id == current_user.id).all()
    return calculations
```

### Read (Retrieve) Calculation

```python
@app.get("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def get_calculation(
    calc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a single calculation by its UUID, if it belongs to the current user.
    """
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")

    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    return calculation
```

### Edit (Update) Calculation

```python
@app.put("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def update_calculation(
    calc_id: str,
    calculation_update: CalculationUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the inputs (and thus the result) of a specific calculation.
    """
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")

    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    if calculation_update.inputs is not None:
        calculation.inputs = calculation_update.inputs
        calculation.result = calculation.get_result()

    calculation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(calculation)
    return calculation
```

### Delete Calculation

```python
@app.delete("/calculations/{calc_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["calculations"])
def delete_calculation(
    calc_id: str,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a calculation by its UUID, if it belongs to the current user.
    """
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")

    calculation = db.query(Calculation).filter(
        Calculation.id == calc_uuid,
        Calculation.user_id == current_user.id
    ).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    db.delete(calculation)
    db.commit()
    return None
```

## Path and Query Parameters

In our endpoints, we used two types of parameters:

1. **Path Parameters**: Variables part of the URL path
   - Example: `/calculations/{calc_id}`
   - Used for identifying a specific resource

2. **Query Parameters**: Variables appended to the URL after a `?`
   - Example: `/calculations?type=addition`
   - Used for filtering, pagination, or other options

Let's add filtering and pagination to our Browse endpoint:

```python
@app.get("/calculations", response_model=List[CalculationResponse], tags=["calculations"])
def list_calculations(
    type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List calculations belonging to the current authenticated user.
    
    Parameters:
    - type: Filter by calculation type (addition, subtraction, etc.)
    - limit: Maximum number of records to return
    - offset: Number of records to skip (for pagination)
    """
    query = db.query(Calculation).filter(Calculation.user_id == current_user.id)
    
    # Apply type filter if provided
    if type:
        query = query.filter(Calculation.type == type.lower())
    
    # Apply pagination
    query = query.order_by(Calculation.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    return query.all()
```

## Error Handling

Notice that in our endpoints, we handle various error cases:

1. **Invalid UUID Format**: When the calculation ID is not a valid UUID
2. **Resource Not Found**: When the calculation doesn't exist or doesn't belong to the current user
3. **Validation Errors**: When the input data doesn't meet our schema requirements
4. **Business Logic Errors**: When the calculation logic throws an error (e.g., division by zero)

This provides a better user experience by giving clear error messages rather than generic 500 errors.

## Security Considerations

Our API endpoints are secured using JWT authentication. Each endpoint requires a valid token, and we also check that the user is only accessing their own resources.

Security best practices implemented:

1. **Authentication**: All endpoints require a valid JWT token
2. **Resource Ownership**: Users can only access their own calculations
3. **Input Validation**: All input data is validated using Pydantic schemas
4. **Error Handling**: Clear error messages without exposing internal details
5. **HTTPS**: In production, all API endpoints should be served over HTTPS

## API Documentation

FastAPI automatically generates API documentation using the OpenAPI specification. When running the application, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These pages provide interactive documentation for your API, including:
- Endpoint descriptions and URLs
- Request and response schemas
- Authentication requirements
- Example requests and responses

## Next Steps

In the next module, we'll integrate our API with a frontend using Jinja2 templates and JavaScript.

## Additional Resources

- [FastAPI Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [FastAPI Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [FastAPI Response Status Codes](https://fastapi.tiangolo.com/tutorial/response-status-code/)
- [REST API Design Best Practices](https://restfulapi.net/)