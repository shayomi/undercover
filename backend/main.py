"""The UnderCover backend."""

import json
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from backend.db import connect, ensure_seeded
from backend.models import Decision, Payment, SignOff, Step

INSTRUCTIONS = Path(__file__).parent / "instructions.md"

Record = dict[str, Any]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_seeded()
    yield


app = FastAPI(title="UnderCover", lifespan=lifespan)


def one(connection: sqlite3.Connection, table: str, key: str) -> Record:
    """Fetch one record's data by its id, or raise a 404."""
    queries = {
        "policy": "SELECT data FROM policies WHERE policy_id = ?",
        "customer": "SELECT data FROM customers WHERE customer_id = ?",
        "plan": "SELECT data FROM plans WHERE plan = ?",
        "add-on": "SELECT data FROM add_ons WHERE add_on = ?",
        "handler": "SELECT data FROM handlers WHERE handler_id = ?",
    }
    row = connection.execute(queries[table], (key,)).fetchone()
    if row is None:
        raise HTTPException(404, f"No {table} {key}")
    return json.loads(row["data"])


def setting(connection: sqlite3.Connection, key: str) -> Any:
    """Read one company setting."""
    row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,))
    return json.loads(row.fetchone()["value"])


def claim_row(connection: sqlite3.Connection, claim_id: str) -> sqlite3.Row:
    """Fetch a claim's row, or raise a 404."""
    row = connection.execute(
        "SELECT * FROM claims WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(404, f"No claim {claim_id}")
    return row


def decision_of(connection: sqlite3.Connection, claim_id: str) -> Record | None:
    """Return the decision on a claim, if there is one."""
    row = connection.execute(
        "SELECT decision, payout, reason, policy_section, signed_off_by "
        "FROM decisions WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()
    return dict(row) if row else None


def payment_of(connection: sqlite3.Connection, claim_id: str) -> Record | None:
    """Return the payment on a claim, if there is one."""
    row = connection.execute(
        "SELECT amount FROM payments WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    return dict(row) if row else None


def set_status(connection: sqlite3.Connection, claim_id: str, status: str) -> None:
    """Move a claim to a new state."""
    connection.execute(
        "UPDATE claims SET status = ? WHERE claim_id = ?", (status, claim_id)
    )


def require_status(row: sqlite3.Row, status: str) -> None:
    """Raise a 409 unless the claim is in the given state."""
    if row["status"] != status:
        raise HTTPException(
            409, f"Claim {row['claim_id']} is {row['status']}, not {status}"
        )


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/claims", operation_id="list_claims")
def list_claims() -> list[Record]:
    """List the claims queue with where each claim stands."""
    with connect() as connection:
        rows = connection.execute(
            "SELECT c.claim_id, c.status, c.data, cu.data AS customer, "
            "d.decision, d.payout FROM claims c "
            "JOIN customers cu ON cu.customer_id = c.customer_id "
            "LEFT JOIN decisions d ON d.claim_id = c.claim_id ORDER BY c.claim_id"
        ).fetchall()
    claims = []
    for row in rows:
        data = json.loads(row["data"])
        claims.append(
            {
                "claim_id": row["claim_id"],
                "claim_type": data["claim_type"],
                "summary": data["summary"],
                "customer_name": json.loads(row["customer"])["name"],
                "amount_claimed": data["amount_claimed"],
                "submitted_on": data["submitted_on"],
                "status": row["status"],
                "decision": row["decision"],
                "payout": row["payout"],
            }
        )
    return claims


@app.get("/api/claims/{claim_id}", operation_id="get_claim")
def get_claim(claim_id: str) -> Record:
    """Get a claim in full, with its policy, decision and payment."""
    with connect() as connection:
        row = claim_row(connection, claim_id)
        customer = one(connection, "customer", row["customer_id"])
        return {
            **json.loads(row["data"]),
            "status": row["status"],
            "policy": one(connection, "policy", row["policy_id"]),
            "customer": {
                "name": customer["name"],
                "previous_claims": customer["previous_claims"],
            },
            "decision": decision_of(connection, claim_id),
            "payment": payment_of(connection, claim_id),
        }


@app.get("/api/policies/{policy_id}", operation_id="get_policy")
def get_policy(policy_id: str) -> Record:
    """Get a policy with its plan's limits and the add-ons it includes."""
    with connect() as connection:
        policy = one(connection, "policy", policy_id)
        return {
            **policy,
            "plan_details": one(connection, "plan", policy["plan"]),
            "deductible_applies_to": setting(connection, "deductible_applies_to"),
            "add_on_details": [
                one(connection, "add-on", add_on) for add_on in policy["add_ons"]
            ],
        }


@app.get("/api/customers/{customer_id}/claim-history", operation_id="get_claim_history")
def get_claim_history(customer_id: str) -> Record:
    """Get a customer's earlier claims, without their contact details."""
    with connect() as connection:
        customer = one(connection, "customer", customer_id)
    return {
        "customer_id": customer_id,
        "customer_since": customer["customer_since"],
        "previous_claims": customer["previous_claims"],
    }


@app.get("/api/policy-wording", operation_id="get_policy_wording")
def get_policy_wording() -> dict[str, str]:
    """Get the policy wording, the contract with the customer."""
    with connect() as connection:
        return {"text": setting(connection, "policy_wording")}


@app.get("/api/instructions", operation_id="get_instructions")
def get_instructions() -> dict[str, str]:
    """Get the UnderCover Agent's instructions."""
    return {"text": INSTRUCTIONS.read_text(encoding="utf-8")}


@app.get("/api/handlers", operation_id="list_handlers")
def list_handlers() -> list[Record]:
    """List the claims handlers and whether each can sign off large payouts."""
    with connect() as connection:
        rows = connection.execute(
            "SELECT data FROM handlers ORDER BY handler_id"
        ).fetchall()
    keys = ("handler_id", "name", "role", "can_approve_over_limit")
    return [{k: json.loads(row["data"])[k] for k in keys} for row in rows]


@app.post("/api/claims/{claim_id}/start", operation_id="start_claim")
def start_claim(claim_id: str) -> Record:
    """Start work on a waiting claim."""
    with connect() as connection:
        require_status(claim_row(connection, claim_id), "waiting")
        set_status(connection, claim_id, "in_progress")
    return {"claim_id": claim_id, "status": "in_progress"}


@app.post("/api/claims/{claim_id}/release", operation_id="release_claim")
def release_claim(claim_id: str) -> Record:
    """Put a claim that is in progress back in the queue."""
    with connect() as connection:
        require_status(claim_row(connection, claim_id), "in_progress")
        set_status(connection, claim_id, "waiting")
    return {"claim_id": claim_id, "status": "waiting"}


@app.post("/api/claims/{claim_id}/decision", operation_id="record_decision")
def record_decision(claim_id: str, decision: Decision) -> Record:
    """Record the decision on a claim that is in progress."""
    payout = round(decision.payout, 2)
    with connect() as connection:
        require_status(claim_row(connection, claim_id), "in_progress")
        limit = setting(connection, "company")["payout_approval_limit"]
        over_limit = decision.decision == "approve" and payout > limit
        status = "awaiting_sign_off" if over_limit else "decided"
        connection.execute(
            "INSERT INTO decisions (claim_id, decision, payout, reason, "
            "policy_section) VALUES (?, ?, ?, ?, ?)",
            (
                claim_id,
                decision.decision,
                payout,
                decision.reason,
                decision.policy_section,
            ),
        )
        set_status(connection, claim_id, status)
    return {"claim_id": claim_id, "status": status}


@app.post("/api/claims/{claim_id}/payment", operation_id="pay_claim")
def pay_claim(claim_id: str, payment: Payment) -> Record:
    """Pay the approved payout on a claim."""
    with connect() as connection:
        row = claim_row(connection, claim_id)
        decision = decision_of(connection, claim_id)
        if decision is None or decision["decision"] != "approve":
            raise HTTPException(409, "Only an approved claim can be paid")
        if payment_of(connection, claim_id):
            raise HTTPException(409, "This claim has already been paid")
        if row["status"] == "awaiting_sign_off":
            raise HTTPException(409, "Needs a handler's sign-off")
        if round(payment.amount, 2) != decision["payout"]:
            raise HTTPException(
                409, f"The amount must be the approved payout of {decision['payout']}"
            )
        connection.execute(
            "INSERT INTO payments VALUES (?, ?)", (claim_id, decision["payout"])
        )
    return {"claim_id": claim_id, "paid": decision["payout"]}


@app.post("/api/claims/{claim_id}/sign-off", operation_id="sign_off_claim")
def sign_off_claim(claim_id: str, sign_off: SignOff) -> Record:
    """Sign off and pay an approved payout over the approval limit."""
    with connect() as connection:
        require_status(claim_row(connection, claim_id), "awaiting_sign_off")
        handler = one(connection, "handler", sign_off.handler_id)
        if not handler["can_approve_over_limit"]:
            raise HTTPException(403, f"{handler['name']} cannot sign off this payout")
        connection.execute(
            "UPDATE decisions SET signed_off_by = ? WHERE claim_id = ?",
            (handler["name"], claim_id),
        )
        connection.execute(
            "INSERT INTO payments SELECT claim_id, payout FROM decisions "
            "WHERE claim_id = ?",
            (claim_id,),
        )
        set_status(connection, claim_id, "decided")
    return {"claim_id": claim_id, "status": "decided", "signed_off_by": handler["name"]}


@app.get("/api/claims/{claim_id}/steps", operation_id="list_steps")
def list_steps(claim_id: str) -> list[Record]:
    """List the agent's steps on a claim, in order."""
    with connect() as connection:
        claim_row(connection, claim_id)
        rows = connection.execute(
            "SELECT id, kind, text FROM steps WHERE claim_id = ? ORDER BY id",
            (claim_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/claims/{claim_id}/steps", operation_id="add_step")
def add_step(claim_id: str, step: Step) -> Record:
    """Add a step to the agent's activity on a claim."""
    with connect() as connection:
        claim_row(connection, claim_id)
        cursor = connection.execute(
            "INSERT INTO steps (claim_id, kind, text) VALUES (?, ?, ?)",
            (claim_id, step.kind, step.text),
        )
    return {"id": cursor.lastrowid, "kind": step.kind, "text": step.text}
