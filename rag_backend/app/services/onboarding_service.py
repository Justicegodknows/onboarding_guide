# onboarding_service.py
# 6-step onboarding tracker


class OnboardingService:
    def __init__(self, steps: int = 6):
        self.steps = steps
        self.user_progress = {}  # user_id: progress

    def get_progress(self, user_id: str):
        progress = self.user_progress.get(user_id, 0)
        status = "incomplete" if progress < self.steps else "complete"
        return {"step": progress, "status": status}

    def complete_step(self, user_id: str, step_id: int):
        progress = self.user_progress.get(user_id, 0)
        if step_id == progress + 1 and progress < self.steps:
            self.user_progress[user_id] = progress + 1
        return self.get_progress(user_id)
