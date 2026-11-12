"""The UnderCover Agent."""

import json
import os
from dataclasses import dataclass
from typing import Any, Literal, cast

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, AgentState, ToolCallRequest
from langchain.tools import ToolRuntime
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from pydantic import SecretStr

load_dotenv(override=True)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-6-luna"
STEP_LENGTH = 400


@dataclass
class Claim:
    """The claim the agent is working on."""

    claim_id: str


def backend() -> httpx.Client:
    """Return a client for the UnderCover backend."""
    url = os.getenv("UNDERCOVER_BACKEND_URL") or "http://localhost:8000"
    return httpx.Client(base_url=url, timeout=30)


def call(method: str, path: str, body: dict[str, Any] | None = None) -> str:
    """Call the backend and return its reply, or its refusal, as text."""
    with backend() as client:
        response = client.request(method, path, json=body)
    if response.is_error:
        return f"Refused ({response.status_code}): {response.json()['detail']}"
    return response.text


def add_step(claim_id: str, kind: str, text: str) -> None:
    """Log one step of the agent's work on the claim."""
    call("POST", f"/api/claims/{claim_id}/steps", {"kind": kind, "text": text})


@tool
def get_claim(claim_id: str) -> str:
    """Get a claim in full: the story, items, documents and the policy."""
    return call("GET", f"/api/claims/{claim_id}")


@tool
def get_policy(policy_id: str) -> str:
    """Get a policy with its plan's limits, deductible and add-ons."""
    return call("GET", f"/api/policies/{policy_id}")


@tool
def get_claim_history(customer_id: str) -> str:
    """Get a customer's earlier claims."""
    return call("GET", f"/api/customers/{customer_id}/claim-history")


@tool
def get_policy_wording() -> str:
    """Get the policy wording, the contract that decides every claim."""
    return json.loads(call("GET", "/api/policy-wording"))["text"]


@tool
def record_decision(
    decision: Literal["approve", "decline", "refer"],
    payout: float,
    reason: str,
    policy_section: str,
    runtime: ToolRuntime[Claim],
) -> str:
    """Record the decision on this claim, with the payout in US dollars."""
    body = {
        "decision": decision,
        "payout": payout,
        "reason": reason,
        "policy_section": policy_section,
    }
    return call("POST", f"/api/claims/{runtime.context.claim_id}/decision", body)


@tool
def pay_claim(amount: float, runtime: ToolRuntime[Claim]) -> str:
    """Pay the approved payout on this claim."""
    path = f"/api/claims/{runtime.context.claim_id}/payment"
    return call("POST", path, {"amount": amount})


TOOLS = [
    get_claim,
    get_policy,
    get_claim_history,
    get_policy_wording,
    record_decision,
    pay_claim,
]


class ActivityLog(AgentMiddleware[AgentState[Any], Claim]):
    """Log each tool call and its result as the agent's steps."""

    def wrap_tool_call(self, request: ToolCallRequest, handler):  # noqa: ANN001
        claim_id = cast(Claim, request.runtime.context).claim_id
        name = request.tool_call["name"]
        args = ", ".join(f"{k}={v}" for k, v in request.tool_call["args"].items())
        add_step(claim_id, "tool_call", f"{name}({args})")
        result: ToolMessage | Command = handler(request)
        if isinstance(result, ToolMessage):
            add_step(claim_id, "tool_result", result.text[:STEP_LENGTH])
        return result


def model() -> ChatOpenAI:
    """Return the model named in MODEL_NAME, or GPT-6 Luna by default."""
    name = os.getenv("MODEL_NAME")
    return ChatOpenAI(
        model=name or DEFAULT_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        reasoning_effort=None if name else "low",
    )


def run(claim_id: str, thread_id: str, llm: BaseChatModel | None = None) -> str:
    """Run the agent on one claim and return its final reply."""
    with backend() as client:
        client.post(f"/api/claims/{claim_id}/start").raise_for_status()
        instructions = client.get("/api/instructions").json()["text"]
    agent = create_agent(
        llm or model(),
        tools=TOOLS,
        system_prompt=instructions,
        middleware=[ActivityLog()],
        context_schema=Claim,
    )
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": f"Decide claim {claim_id}."}]},
            config={"configurable": {"thread_id": thread_id}},
            context=Claim(claim_id),
        )
    except Exception as error:
        add_step(claim_id, "error", f"The agent stopped: {error}")
        call("POST", f"/api/claims/{claim_id}/release")
        raise
    answer = result["messages"][-1].text
    add_step(claim_id, "answer", answer)
    return answer
