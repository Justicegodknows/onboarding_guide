
from fastapi import APIRouter, Path
from app.models.schemas import OnboardingProgress
from app.services.onboarding_service import OnboardingService


router = APIRouter(prefix="/api/v1/onboarding")
service = OnboardingService()



# GET /api/v1/onboarding/{user_id}
@router.get("/{user_id}")
def get_onboarding_progress(user_id: str = Path(..., description="User ID")):
    progress = service.get_progress(user_id)
    return OnboardingProgress(step=progress["step"], status=progress["status"])



# POST /api/v1/onboarding/{user_id}/complete/{step_id}
@router.post("/{user_id}/complete/{step_id}")
def complete_onboarding_step(
    user_id: str = Path(..., description="User ID"),
    step_id: int = Path(..., description="Step ID")
):
    progress = service.complete_step(user_id, step_id)
    return OnboardingProgress(step=progress["step"], status=progress["status"])
