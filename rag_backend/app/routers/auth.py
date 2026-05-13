from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password, get_current_user
from app.db import SessionLocal
from app.models.db_models import AuthUser

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    dept: str = Field(default="General")
    display_name: str = Field(default="")


@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(AuthUser).filter(AuthUser.email == form_data.username.lower().strip()).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role,
            "dept": user.dept,
            "display_name": user.display_name or user.email,
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.email,
        "role": user.role,
        "dept": user.dept,
        "display_name": user.display_name or user.email,
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_employee(payload: RegisterRequest, db: Session = Depends(get_db)):
    normalized_email = payload.email.lower().strip()

    if "@" not in normalized_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid email is required",
        )

    existing = db.query(AuthUser).filter(AuthUser.email == normalized_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    user = AuthUser(
        email=normalized_email,
        password_hash=get_password_hash(payload.password),
        role="USER",
        dept=payload.dept,
        display_name=payload.display_name or normalized_email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Employee account created",
        "user": {
            "username": user.email,
            "role": user.role,
            "dept": user.dept,
            "display_name": user.display_name,
        },
    }


@router.get("/me")
async def read_users_me(current_user=Depends(get_current_user)):
    return current_user
