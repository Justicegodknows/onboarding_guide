from fastapi import FastAPI
from app.routers import health, chat, documents, onboarding

app = FastAPI()

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(onboarding.router)
