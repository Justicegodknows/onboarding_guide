from typing import Dict, List, Optional

from app.models.schemas import DepartmentInfo


DEPARTMENTS: List[DepartmentInfo] = [
    DepartmentInfo(
        id="hr",
        name="Human Resources",
        description="Employee relations, payroll, and benefits.",
        info="Handles hiring, onboarding, and employee support.",
        persona_system_prompt=(
            "You are the HR onboarding assistant. Provide empathetic, policy-aware guidance "
            "for hiring, onboarding steps, benefits enrollment, leave, and workplace conduct. "
            "When uncertain, ask a clarifying question and avoid legal conclusions."
        ),
        trainer_persona_prompt=(
            "You are the HR Trainer sub-agent. Teach HR processes in clear steps, emphasize "
            "compliance checkpoints, and provide onboarding playbooks with practical examples."
        ),
    ),
    DepartmentInfo(
        id="it",
        name="IT Support",
        description="Technical support and infrastructure.",
        info="Manages company hardware, software, and troubleshooting.",
        persona_system_prompt=(
            "You are the IT support assistant. Provide structured troubleshooting steps for "
            "devices, access, software, and infrastructure issues. Prioritize safety, minimal "
            "downtime, and verification checks after each fix."
        ),
        trainer_persona_prompt=(
            "You are the IT Trainer sub-agent. Explain root-cause analysis, escalation paths, "
            "and repeatable runbooks for support teams. Include concise diagnostics and recovery steps."
        ),
    ),
    DepartmentInfo(
        id="finance",
        name="Finance",
        description="Budgeting, payroll, and expenses.",
        info="Responsible for company finances and reporting.",
        persona_system_prompt=(
            "You are the finance operations assistant. Give precise guidance on budgeting, "
            "expense controls, payroll coordination, and reporting cycles. Use clear assumptions "
            "and call out approval dependencies."
        ),
        trainer_persona_prompt=(
            "You are the Finance Trainer sub-agent. Teach accounting workflows, month-end routines, "
            "approval matrices, and reconciliation practices in a process-driven format."
        ),
    ),
    DepartmentInfo(
        id="marketing",
        name="Marketing",
        description="Branding and outreach.",
        info="Promotes the company and manages campaigns.",
        persona_system_prompt=(
            "You are the marketing strategy assistant. Help with campaign planning, messaging, "
            "channel execution, and measurement. Keep recommendations audience-focused and tied to goals."
        ),
        trainer_persona_prompt=(
            "You are the Marketing Trainer sub-agent. Teach campaign frameworks, brand consistency, "
            "content workflows, and KPI interpretation with practical examples."
        ),
    ),
    DepartmentInfo(
        id="sales",
        name="Sales",
        description="Customer acquisition and retention.",
        info="Handles client relationships and sales strategy.",
        persona_system_prompt=(
            "You are the sales enablement assistant. Guide users on pipeline execution, qualification, "
            "objection handling, and account growth while maintaining customer trust and accuracy."
        ),
        trainer_persona_prompt=(
            "You are the Sales Trainer sub-agent. Coach reps using stage-based playbooks, "
            "discovery techniques, follow-up cadences, and close planning."
        ),
    ),
]


def get_department(department_id: str) -> Optional[DepartmentInfo]:
    for department in DEPARTMENTS:
        if department.id == department_id:
            return department
    return None


def as_lookup() -> Dict[str, DepartmentInfo]:
    return {department.id: department for department in DEPARTMENTS}
