import runpy
import sys

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

import backend.main
from agent import main
from backend import db
from backend.main import app

real_backend = main.backend


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies in place of a real model."""

    def bind_tools(self, tools, **kwargs):
        return self


def calls(*tool_calls, answer="Approved $420.00."):
    """Script one tool call per reply, then a final answer."""
    replies = [
        AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": str(i)}])
        for i, (name, args) in enumerate(tool_calls)
    ]
    return StubModel(messages=iter([*replies, AIMessage(content=answer)]))


def decision(payout):
    return (
        "record_decision",
        {
            "decision": "approve",
            "payout": payout,
            "reason": "The delay is covered. The costs are within the limit.",
            "policy_section": "Section 3. Trip Delay",
        },
    )


@pytest.fixture(autouse=True)
def local_backend(monkeypatch):
    monkeypatch.setattr(main, "backend", lambda: TestClient(app))


def claim(client):
    return client.get("/api/claims/CLM-1001").json()


def steps(client):
    return client.get("/api/claims/CLM-1001/steps").json()


def test_the_agent_reads_decides_and_pays(client):
    stub = calls(
        ("get_claim", {"claim_id": "CLM-1001"}),
        ("get_policy", {"policy_id": "POL-2001"}),
        ("get_claim_history", {"customer_id": "CUS-3001"}),
        ("get_policy_wording", {}),
        decision(420.0),
        ("pay_claim", {"amount": 420.0}),
    )
    assert main.run("CLM-1001", "thread-1", stub) == "Approved $420.00."
    result = claim(client)
    assert result["status"] == "decided"
    assert result["payment"] == {"amount": 420.0}
    logged = steps(client)
    assert [s["kind"] for s in logged] == ["tool_call", "tool_result"] * 6 + ["answer"]
    assert logged[0]["text"] == "get_claim(claim_id=CLM-1001)"
    assert "Policy Wording" in logged[7]["text"]
    assert logged[-1]["text"] == "Approved $420.00."


def test_the_payment_over_the_limit_is_blocked(client):
    stub = calls(decision(1250.0), ("pay_claim", {"amount": 1250.0}))
    main.run("CLM-1001", "thread-1", stub)
    result = claim(client)
    assert result["status"] == "awaiting_sign_off"
    assert result["payment"] is None
    assert steps(client)[3]["text"] == "Refused (409): Needs a handler's sign-off"


def test_a_failed_run_puts_the_claim_back(client):
    with pytest.raises(Exception):  # noqa: B017, PT011
        main.run("CLM-1001", "thread-1", StubModel(messages=iter([])))
    assert claim(client)["status"] == "waiting"
    assert steps(client)[-1]["kind"] == "error"


def test_run_agent_from_the_backend(client, monkeypatch):
    def stubbed_run(claim_id, thread_id):
        return main.run(claim_id, thread_id, calls(decision(420.0)))

    monkeypatch.setattr(backend.main, "run", stubbed_run)
    response = client.post("/api/claims/CLM-1001/agent-run")
    assert response.status_code == 200
    assert response.json()["thread_id"]
    assert claim(client)["status"] == "decided"


def test_run_agent_only_on_a_waiting_claim(client):
    client.post("/api/claims/CLM-1001/start")
    assert client.post("/api/claims/CLM-1001/agent-run").status_code == 409


def test_command_line(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["agent", "CLM-1001"])
    monkeypatch.setattr(main, "model", lambda: calls(decision(420.0)))
    runpy.run_module("agent", run_name="__main__")
    assert "Approved $420.00." in capsys.readouterr().out


def test_command_line_takes_one_claim_id_at_most(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["agent", "CLM-1001", "CLM-1002"])
    with pytest.raises(SystemExit, match=r"Usage: uv run -m agent \[CLM-1001\]"):
        runpy.run_module("agent", run_name="__main__")


def test_command_line_works_the_queue(client, monkeypatch, capsys):
    with db.connect() as connection:
        connection.execute(
            "UPDATE claims SET status = 'decided' "
            "WHERE claim_id NOT IN ('CLM-1001', 'CLM-1002', 'CLM-1003')"
        )
    replies = {
        "CLM-1001": calls(decision(420.0), answer="Approved $420.00."),
        "CLM-1002": StubModel(messages=iter([])),
        "CLM-1003": calls(answer="Referred."),
    }
    started = []

    def model_for_next_claim():
        claim_id = ["CLM-1001", "CLM-1002", "CLM-1003"][len(started)]
        started.append(claim_id)
        return replies[claim_id]

    monkeypatch.setattr(sys, "argv", ["agent"])
    monkeypatch.setattr(main, "model", model_for_next_claim)
    runpy.run_module("agent", run_name="__main__")

    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "3 claims waiting"
    assert lines[1] == "[1/3] CLM-1001: Approved $420.00."
    assert lines[2].startswith("[2/3] CLM-1002: stopped:")
    assert lines[3] == "[3/3] CLM-1003: Referred."
    assert claim(client)["status"] == "decided"
    statuses = {c["claim_id"]: c["status"] for c in client.get("/api/claims").json()}
    assert statuses["CLM-1002"] == "waiting"


def test_waiting_claims_skips_the_rest(client):
    client.post("/api/claims/CLM-1001/start")
    waiting = main.waiting_claims()
    assert len(waiting) == 24
    assert "CLM-1001" not in waiting
    assert waiting == sorted(waiting)


def test_backend_url(monkeypatch):
    monkeypatch.setenv("UNDERCOVER_BACKEND_URL", "http://localhost:8001")
    assert str(real_backend().base_url) == "http://localhost:8001"


def test_model_name(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    assert main.model().model_name == "openai/gpt-6-luna"
    monkeypatch.setenv("MODEL_NAME", "openrouter/free")
    assert main.model().model_name == "openrouter/free"
