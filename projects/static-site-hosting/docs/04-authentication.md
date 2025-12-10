# Module 4: Authentication with JWT

## Introduction

In this module, we'll implement user authentication using JSON Web Tokens (JWT). JWT is a compact, URL-safe means of representing claims to be transferred between two parties. In our application, we'll use JWTs to authenticate users and secure API endpoints.

## Objectives

- Understand the JWT authentication flow
- Implement password hashing
- Create JWT token generation and verification
- Implement protected routes with dependencies
- Add token-based authentication to our API

## Understanding JWT Authentication

JWT authentication follows these general steps:

1. User provides credentials (username/password)
2. Server validates credentials
3. Server generates a JWT token and returns it to the client
4. Client includes the token in subsequent requests in an Authorization header
5. Server validates the token and grants access if valid

JWTs consist of three parts:
- Header: Contains the token type and algorithm
- Payload: Contains claims (user information, expiration time, etc.)
- Signature: Used to verify the token hasn't been tampered with

## Implementing Password Hashing

First, let's create a module for password hashing in `app/auth/jwt.py`:

```python
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from uuid import UUID

from app.core.config import get_settings
from app.schemas.token import TokenType

settings = get_settings()

# Set up password hashing with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.
    
    Args:
        plain_password: The plain-text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        bool: True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    Args:
        password: The plain-text password to hash
        
    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)

def create_token(subject: str, token_type: TokenType) -> str:
    """
    Create a JWT token with the given subject and type.
    
    Args:
        subject: The subject of the token (usually user ID)
        token_type: The type of token (access or refresh)
        
    Returns:
        str: JWT token
    """
    if token_type == TokenType.ACCESS:
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    else:  # TokenType.REFRESH
        expire_minutes = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    
    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": token_type
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt
```

## Creating Authentication Dependencies

Now, let's create dependencies that will be used to protect routes in `app/auth/dependencies.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config import get_settings
from app.database import get_db
from app.models.user import User

settings = get_settings()

# OAuth2 scheme for Bearer token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current user from the JWT token.
    
    Args:
        token: JWT token from the Authorization header
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If the token is invalid or the user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Convert the user_id to UUID
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    # Get the user from the database
    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User: The authenticated active user
        
    Raises:
        HTTPException: If the user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user
```

## Implementing Authentication Endpoints

Now, let's implement the authentication endpoints in `app/main.py`:

```python
# User Registration Endpoint
@app.post(
    "/auth/register", 
    response_model=UserResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=["auth"]
)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    """
    user_data = user_create.dict(exclude={"confirm_password"})
    try:
        user = User.register(db, user_data)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# User Login Endpoints
@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Login with JSON payload (username & password).
    Returns an access token, refresh token, and user info.
    """
    auth_result = User.authenticate(db, user_login.username, user_login.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_result["user"]
    db.commit()  # commit the last_login update

    # Ensure expires_at is timezone-aware
    expires_at = auth_result.get("expires_at")
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    return TokenResponse(
        access_token=auth_result["access_token"],
        refresh_token=auth_result["refresh_token"],
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified
    )

@app.post("/auth/token", tags=["auth"])
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login with form data (Swagger/UI).
    Returns an access token.
    """
    auth_result = User.authenticate(db, form_data.username, form_data.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": auth_result["access_token"],
        "token_type": "bearer"
    }
```

## Implementing User Authentication Methods

Let's add the authentication methods to our User model:

```python
@classmethod
def register(cls, db, user_data: dict):
    """
    Register a new user.

    Args:
        db: SQLAlchemy database session
        user_data: Dictionary containing user registration data
        
    Returns:
        User: The newly created user instance
        
    Raises:
        ValueError: If password is invalid or username/email already exists
    """
    password = user_data.get("password")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    
    # Check for duplicate email or username
    existing_user = db.query(cls).filter(
        or_(cls.email == user_data["email"], cls.username == user_data["username"])
    ).first()
    if existing_user:
        raise ValueError("Username or email already exists")
    
    # Create new user instance
    hashed_password = cls.hash_password(password)
    user = cls(
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        email=user_data["email"],
        username=user_data["username"],
        password=hashed_password,
        is_active=True,
        is_verified=False
    )
    db.add(user)
    return user

@classmethod
def authenticate(cls, db, username_or_email: str, password: str):
    """
    Authenticate a user by username/email and password.
    
    Args:
        db: SQLAlchemy database session
        username_or_email: Username or email to authenticate
        password: Password to verify
        
    Returns:
        dict: Authentication result with tokens and user data, or None if authentication fails
    """
    user = db.query(cls).filter(
        or_(cls.username == username_or_email, cls.email == username_or_email)
    ).first()

    if not user or not user.verify_password(password):
        return None

    # Update the last_login timestamp
    user.last_login = utcnow()
    db.flush()

    # Generate tokens
    access_token = cls.create_access_token({"sub": str(user.id)})
    refresh_token = cls.create_refresh_token({"sub": str(user.id)})
    expires_at = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_at": expires_at,
        "user": user
    }
```

## Protecting API Routes

Now we can protect our API routes using the dependencies we created. Here's an example with the calculations endpoints:

```python
@app.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["calculations"],
)
def create_calculation(
    calculation_data: CalculationBase,
    current_user = Depends(get_current_active_user),  # Protected route
    db: Session = Depends(get_db)
):
    """
    Create a new calculation for the authenticated user.
    Automatically computes the 'result'.
    """
    try:
        new_calculation = Calculation.create(
            calculation_type=calculation_data.type,
            user_id=current_user.id,  # Use current user's ID
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

## JWT Security Considerations

When implementing JWT authentication, keep these security considerations in mind:

1. **Secret Key**: Use a strong, unique secret key for signing JWTs
2. **Token Expiration**: Set appropriate expiration times for tokens
3. **HTTPS**: Always use HTTPS in production to protect tokens in transit
4. **Token Storage**: Advise clients to store tokens securely (e.g., HttpOnly cookies)
5. **Token Revocation**: Consider implementing a token blacklist for logout/revocation
6. **Claims**: Include only necessary information in the token payload

## Next Steps

In the next module, we'll implement the API endpoints for our calculator application using the authentication we've set up.

## Additional Resources

- [JSON Web Tokens (JWT)](https://jwt.io/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Passlib Documentation](https://passlib.readthedocs.io/en/stable/)
- [Python-JOSE Documentation](https://python-jose.readthedocs.io/en/latest/)