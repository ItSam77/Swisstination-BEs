from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid
from datetime import datetime, timedelta
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from supabase_client import supabase

router = APIRouter(prefix="/auth", tags=["Authentication"])

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()

class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    message: str
    user: dict = None
    session: dict = None
    access_token: str = None
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: str = None
    user_id: str = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(email=email, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    result = supabase.table("custom_users").select("*").eq("user_id", token_data.user_id).execute()
    if not result.data:
        raise credentials_exception
    
    user = result.data[0]
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "created_at": user.get("created_at")
    }

@router.post("/signup", response_model=AuthResponse)
async def signup(user_data: UserSignup):
    try:
        print(f"Signup attempt for email: {user_data.email}")  # Debug log
        
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured. Please set up Supabase credentials."
            )
        
        existing_user = supabase.table("custom_users").select("*").eq("email", user_data.email).execute()
        
        if existing_user.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        hashed_password = get_password_hash(user_data.password)
        
        user_id = str(uuid.uuid4())
        new_user = {
            "user_id": user_id,
            "name": user_data.name,
            "email": user_data.email,
            "password": hashed_password,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("custom_users").insert(new_user).execute()
        print(f"Insert result: {result}")  # Debug log
        
        if result.data:
            user_data_response = {
                "user_id": user_id,
                "name": user_data.name,
                "email": user_data.email,
                "created_at": new_user["created_at"]
            }
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user_data.email, "user_id": user_id}, 
                expires_delta=access_token_expires
            )
            
            return AuthResponse(
                message="Signup successful!",
                user=user_data_response,
                session={"user_id": user_id, "email": user_data.email},
                access_token=access_token
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {str(e)}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )

@router.post("/login", response_model=AuthResponse)
async def login(user_credentials: UserLogin):
    try:
        print(f"Login attempt for email: {user_credentials.email}")  # Debug log
        
        if supabase is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not configured. Please set up Supabase credentials."
            )
        
        result = supabase.table("custom_users").select("*").eq("email", user_credentials.email).execute()
        print(f"Login query result: {result}")  # Debug log
        
        if result.data:
            user = result.data[0]
            
            if verify_password(user_credentials.password, user["password"]):
                user_data_response = {
                    "user_id": user["user_id"],
                    "name": user["name"],
                    "email": user["email"],
                    "created_at": user.get("created_at")
                }
                
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={"sub": user["email"], "user_id": user["user_id"]}, 
                    expires_delta=access_token_expires
                )
                
                return AuthResponse(
                    message="Login successful!",
                    user=user_data_response,
                    session={"user_id": user["user_id"], "email": user["email"]},
                    access_token=access_token
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout")
async def logout():
    return {"message": "Logout successful"}

@router.get("/user")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    return {
        "message": "User authenticated successfully",
        "user": current_user
    }

@router.get("/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    return {
        "valid": True,
        "user": current_user
    }

@router.get("/test")
async def test_connection():
    return {"message": "Backend is working!", "timestamp": datetime.utcnow().isoformat()}