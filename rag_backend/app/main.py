
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, chat, documents, onboarding, ingest, trainer, departments


app = FastAPI()

# CORS setup for frontend integration
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:3000"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(onboarding.router)
app.include_router(ingest.router)
app.include_router(trainer.router)
app.include_router(departments.router)
