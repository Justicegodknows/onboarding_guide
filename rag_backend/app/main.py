from contextlib import asynccontextmanager
import json

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.db import Base, SessionLocal, engine
from app.models import db_models  # noqa: F401
from app.models.db_models import AuthUser
from app.routers import auth, health, chat, documents, onboarding, ingest, trainer, departments
from app.routers.integrations import router as integrations_router
from app.core.security import get_password_hash


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all DB tables on startup
    Base.metadata.create_all(bind=engine)

    # Seed initial admin accounts
    db = SessionLocal()
    try:
        existing_admin = db.query(AuthUser).first()
        if not existing_admin:
            db.add(AuthUser(
                email="euzadmin",
                password_hash=get_password_hash("admin"),
                role="ADMIN",
                dept="Administration",
                display_name="EUZ Administrator",
            ))
            db.add(AuthUser(
                email="admin@vaultmind.local",
                password_hash=get_password_hash("admin123"),
                role="ADMIN",
                dept="IT",
                display_name="VaultMind Admin",
            ))
            db.add(AuthUser(
                email="user@vaultmind.local",
                password_hash=get_password_hash("user123"),
                role="USER",
                dept="Finance",
                display_name="Finance User",
            ))
            db.commit()
    finally:
        db.close()

    yield


# ✅ Create app FIRST
app = FastAPI(
    title="EUZ Onboarding API",
    description="RAG-powered onboarding backend",
    version="1.0.0",
    lifespan=lifespan
)

# ✅ Middleware AFTER app is created
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # allow all — Cloudflare handles security
)

cors_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# ✅ CORS preflight handler
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Authorization,Content-Type,Accept",
        },
    )

# ✅ Root routes
@app.get("/")
def root():
    return {"status": "ok", "message": "EUZ Backend is live"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ✅ Include all routers
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(onboarding.router)
app.include_router(ingest.router)
app.include_router(trainer.router)
app.include_router(departments.router)
app.include_router(integrations_router)
