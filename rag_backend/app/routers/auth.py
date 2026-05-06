from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, get_password_hash, verify_password, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Mock user database for demo purposes
# In production, these would be in a proper database
USERS_DB = {
    "admin@vaultmind.local": {
        "username": "admin@vaultmind.local",
        "password": get_password_hash("admin123"),
        "role": "ADMIN",
        "dept": "IT"
    },
    "user@vaultmind.local": {
        "username": "user@vaultmind.local",
        "password": get_password_hash("user123"),
        "role": "USER",
        "dept": "Finance"
    }
}

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    role: str = Field(default="USER")
    dept: str = Field(default="General")

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "dept": user["dept"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_employee(payload: RegisterRequest):
    normalized_email = payload.email.lower().strip()

    if "@" not in normalized_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid email is required",
        )

    if normalized_email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    normalized_role = payload.role.upper()
    if normalized_role not in {"USER", "ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be USER or ADMIN",
        )

    USERS_DB[normalized_email] = {
        "username": normalized_email,
        "password": get_password_hash(payload.password),
        "role": normalized_role,
        "dept": payload.dept,
    }

    return {
        "message": "Employee account created",
        "user": {
            "username": normalized_email,
            "role": normalized_role,
            "dept": payload.dept,
        },
    }

@router.get("/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return current_user
