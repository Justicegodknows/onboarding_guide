"""Tests for department routes and department-specific chat endpoints."""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.departments_service import DEPARTMENTS


def test_list_departments_returns_expected_shape(client):
    response = client.get("/api/v1/departments/")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 1
    assert {
        "id",
        "name",
        "description",
        "info",
        "persona_system_prompt",
        "trainer_persona_prompt",
    }.issubset(payload[0].keys())


def test_get_department_returns_department(client):
    response = client.get("/api/v1/departments/hr")
    assert response.status_code == 200
    assert response.json()["id"] == "hr"


def test_get_department_returns_404_for_unknown_id(client):
    response = client.get("/api/v1/departments/unknown")
    assert response.status_code == 404


def test_department_chat_routes_question_through_rag(client):
    with patch(
        "app.routers.departments.RAGService.generate",
        new_callable=AsyncMock,
        return_value="Department answer",
    ) as mock_generate:
        response = client.post(
            "/api/v1/departments/it/chat",
            json={"question": "How do I reset my laptop?", "history": []},
        )

    assert response.status_code == 200
    assert response.json() == {"answer": "Department answer"}

    context, question = mock_generate.await_args.args[:2]
    assert "IT Support" in context
    assert question.startswith("[IT Support]")
    assert "IT support assistant" in mock_generate.await_args.kwargs["system_prompt"]


def test_department_trainer_routes_question_through_trainer_agent(client):
    with patch(
        "app.routers.departments.TrainerSubAgent.answer",
        new_callable=AsyncMock,
        return_value="Trainer answer",
    ) as mock_answer:
        response = client.post(
            "/api/v1/departments/finance/trainer",
            json={"question": "What does month-end close involve?", "history": ["Previous"]},
        )

    assert response.status_code == 200
    assert response.json() == {"answer": "Trainer answer"}

    kwargs = mock_answer.await_args.kwargs
    assert kwargs["question"].startswith("[Finance]")
    assert kwargs["history"] == ["Previous"]
    assert "Finance Trainer sub-agent" in kwargs["system_prompt_override"]


# ---------------------------------------------------------------------------
# Persona propagation – all departments
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dept", DEPARTMENTS, ids=[d.id for d in DEPARTMENTS])
def test_chat_persona_propagated_for_every_department(client, dept):
    """Each department's persona_system_prompt reaches RAGService.generate()."""
    with patch(
        "app.routers.departments.RAGService.generate",
        new_callable=AsyncMock,
        return_value="ok",
    ) as mock_generate:
        response = client.post(
            f"/api/v1/departments/{dept.id}/chat",
            json={"question": "test question", "history": []},
        )

    assert response.status_code == 200
    passed_system_prompt = mock_generate.await_args.kwargs["system_prompt"]
    assert passed_system_prompt == dept.persona_system_prompt, (
        f"{dept.id}: expected persona_system_prompt to be forwarded verbatim"
    )


@pytest.mark.parametrize("dept", DEPARTMENTS, ids=[d.id for d in DEPARTMENTS])
def test_trainer_persona_propagated_for_every_department(client, dept):
    """Each department's trainer_persona_prompt reaches TrainerSubAgent.answer()."""
    with patch(
        "app.routers.departments.TrainerSubAgent.answer",
        new_callable=AsyncMock,
        return_value="ok",
    ) as mock_answer:
        response = client.post(
            f"/api/v1/departments/{dept.id}/trainer",
            json={"question": "test question", "history": []},
        )

    assert response.status_code == 200
    passed_override = mock_answer.await_args.kwargs["system_prompt_override"]
    assert passed_override == dept.trainer_persona_prompt, (
        f"{dept.id}: expected trainer_persona_prompt to be forwarded verbatim"
    )


@pytest.mark.parametrize("dept", DEPARTMENTS, ids=[d.id for d in DEPARTMENTS])
def test_chat_prefixes_question_with_department_name(client, dept):
    """The department name is prepended to the question before reaching generate()."""
    with patch(
        "app.routers.departments.RAGService.generate",
        new_callable=AsyncMock,
        return_value="ok",
    ) as mock_generate:
        client.post(
            f"/api/v1/departments/{dept.id}/chat",
            json={"question": "anything", "history": []},
        )

    _ctx, forwarded_question = mock_generate.await_args.args[:2]
    assert forwarded_question.startswith(f"[{dept.name}]"), (
        f"{dept.id}: question should be prefixed with '[{dept.name}]'"
    )


@pytest.mark.parametrize("dept", DEPARTMENTS, ids=[d.id for d in DEPARTMENTS])
def test_trainer_prefixes_question_with_department_name(client, dept):
    """The department name is prepended to the question before reaching answer()."""
    with patch(
        "app.routers.departments.TrainerSubAgent.answer",
        new_callable=AsyncMock,
        return_value="ok",
    ) as mock_answer:
        client.post(
            f"/api/v1/departments/{dept.id}/trainer",
            json={"question": "anything", "history": []},
        )

    forwarded_question = mock_answer.await_args.kwargs["question"]
    assert forwarded_question.startswith(f"[{dept.name}]"), (
        f"{dept.id}: question should be prefixed with '[{dept.name}]'"
    )


def test_chat_returns_404_for_unknown_department(client):
    response = client.post(
        "/api/v1/departments/nonexistent/chat",
        json={"question": "hello", "history": []},
    )
    assert response.status_code == 404


def test_trainer_returns_404_for_unknown_department(client):
    response = client.post(
        "/api/v1/departments/nonexistent/trainer",
        json={"question": "hello", "history": []},
    )
    assert response.status_code == 404
