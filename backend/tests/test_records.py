import json
import sqlite3

import pytest

from backend import db
from backend.main import app

TABLE_COUNTS = {
    "claims": 25,
    "policies": 50,
    "customers": 49,
    "plans": 3,
    "handlers": 3,
}


def claim_ids() -> set[str]:
    with db.connect() as connection:
        return {r[0] for r in connection.execute("SELECT claim_id FROM claims")}


@pytest.mark.parametrize(("table", "expected"), TABLE_COUNTS.items())
def test_seed_counts(table, expected):
    with db.connect() as connection:
        rows = connection.execute(f"SELECT * FROM {table}").fetchall()  # noqa: S608
    assert len(rows) == expected


def test_seed_never_reads_held_out_data(monkeypatch):
    opened = []
    original = db.Path.read_text

    def spy(path, *args, **kwargs):
        opened.append(str(path))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(db.Path, "read_text", spy)
    db.seed()
    assert opened
    assert not [p for p in opened if "evals" in p or "security" in p]


def test_the_queue_is_exactly_the_claims_file():
    queue = json.loads((db.DATA / "claims.json").read_text())
    assert claim_ids() == {c["claim_id"] for c in queue}
    assert "CLM-1901" not in claim_ids()


def test_ensure_seeded_keeps_an_existing_database():
    with db.connect() as connection:
        connection.execute("UPDATE claims SET status = 'decided'")
    db.ensure_seeded()
    with db.connect() as connection:
        statuses = {r[0] for r in connection.execute("SELECT status FROM claims")}
    assert statuses == {"decided"}


def test_list_claims(client):
    claims = client.get("/api/claims").json()
    assert len(claims) == 25
    first = claims[0]
    assert first["claim_id"] == "CLM-1001"
    assert first["customer_name"] == "Maya Patel"
    assert first["amount_claimed"] == 420.0
    assert first["submitted_on"] == "2026-06-24"
    assert first["claim_type"] == "trip_delay"
    assert {c["status"] for c in claims} == {"waiting"}


def test_get_claim(client):
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["story"].startswith("My flight home from Rome")
    assert len(claim["items"]) == 3
    assert claim["documents"]
    assert claim["policy"]["plan"] == "premium"
    assert claim["customer"]["name"] == "Maya Patel"
    assert claim["status"] == "waiting"
    assert claim["decision"] is None
    assert claim["payment"] is None


def test_get_policy(client):
    policy = client.get("/api/policies/POL-2001").json()
    assert policy["plan_details"]["deductible"] == 50.0
    assert policy["plan_details"]["trip_delay_max"] == 800.0
    assert policy["deductible_applies_to"] == ["baggage", "emergency_medical"]
    assert policy["add_on_details"] == []


def test_get_policy_with_add_ons(client):
    policies = json.loads((db.DATA / "policies.json").read_text())
    with_add_on = next(p for p in policies if p["add_ons"])
    policy = client.get(f"/api/policies/{with_add_on['policy_id']}").json()
    assert [a["add_on"] for a in policy["add_on_details"]] == with_add_on["add_ons"]


def test_claim_history_has_no_contact_details(client):
    history = client.get("/api/customers/CUS-3001/claim-history").json()
    assert [c["claim_id"] for c in history["previous_claims"]] == ["CLM-0412"]
    text = json.dumps(history)
    for private in ("email", "phone", "address", "date_of_birth", "Jersey City"):
        assert private not in text


def test_policy_wording(client):
    text = client.get("/api/policy-wording").json()["text"]
    assert text == (db.DATA / "policy_wording.md").read_text()
    assert "Claims Manual" not in text


def test_instructions(client):
    assert "UnderCover Agent" in client.get("/api/instructions").json()["text"]


def test_handlers(client):
    handlers = client.get("/api/handlers").json()
    assert len(handlers) == 3
    assert "email" not in handlers[0]
    assert handlers[0]["name"] == "Dana Whitfield"


@pytest.mark.parametrize(
    "path",
    [
        "/api/claims/CLM-0000",
        "/api/policies/POL-0000",
        "/api/customers/CUS-0000/claim-history",
        "/api/claims/CLM-0000/steps",
    ],
)
def test_unknown_records_are_404(client, path):
    assert client.get(path).status_code == 404


def test_every_operation_has_an_id_and_a_one_line_docstring(client):
    schema = client.get("/openapi.json").json()
    operations = [op for path in schema["paths"].values() for op in path.values()]
    assert len(operations) >= 15
    for operation in operations:
        assert operation["operationId"]
        assert operation["description"]
        assert "\n" not in operation["description"]
        for parameter in operation.get("parameters", []):
            assert parameter["required"]
    assert len({op["operationId"] for op in operations}) == len(operations)


def test_routes_are_all_in_the_schema():
    paths = {getattr(r, "path", "") for r in app.routes}
    assert "/api/claims/{claim_id}/payment" in paths


def test_connection_closes():
    with db.connect() as connection:
        pass
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")
