
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, SessionLocal, engine
from app.models import db_models  # noqa: F401 — import side-effects register all ORM models
from app.models.db_models import AuthUser
from app.routers import auth, health, chat, documents, onboarding, ingest, trainer, departments
from app.routers.integrations import router as integrations_router
from app.core.security import get_password_hash


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all DB tables on startup (idempotent — safe to call multiple times)
    Base.metadata.create_all(bind=engine)

    # Seed an initial admin account when the auth store is empty.
    db = SessionLocal()
    try:
        existing_admin = db.query(AuthUser).first()
        if not existing_admin:
            db.add(
                AuthUser(
                    email="euzadmin",
                    password_hash=get_password_hash("admin"),
                    role="ADMIN",
                    dept="Administration",
                    display_name="EUZ Administrator",
                )
            )
            db.add(
                AuthUser(
                    email="admin@vaultmind.local",
                    password_hash=get_password_hash("admin123"),
                    role="ADMIN",
                    dept="IT",
                    display_name="VaultMind Admin",
                )
            )
            db.add(
                AuthUser(
                    email="user@vaultmind.local",
                    password_hash=get_password_hash("user123"),
                    role="USER",
                    dept="Finance",
                    display_name="Finance User",
                )
            )
            db.commit()
    finally:
        db.close()

    yield


app = FastAPI(lifespan=lifespan)

# CORS setup for frontend integration
# Allow all origins for local development and dev tunnel hosts.
# If you need a stricter policy in production, set CORS_ORIGINS in rag_backend/.env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(onboarding.router)
app.include_router(ingest.router)
app.include_router(trainer.router)
app.include_router(departments.router)
app.include_router(integrations_router)
