import runpy

import pytest

from backend import db

APPROVE = {
    "decision": "approve",
    "payout": 420.0,
    "reason": "The flight was canceled for a crew problem. The costs are covered.",
    "policy_section": "Section 3. Trip Delay",
}
OVER_LIMIT = {**APPROVE, "payout": 1250.0}
DECLINE = {**APPROVE, "decision": "decline", "payout": 0}
REFER = {**APPROVE, "decision": "refer", "payout": 0}


def decide(client, decision, claim_id="CLM-1001"):
    assert client.post(f"/api/claims/{claim_id}/start").status_code == 200
    response = client.post(f"/api/claims/{claim_id}/decision", json=decision)
    assert response.status_code == 200
    return response.json()


def pay(client, amount, claim_id="CLM-1001"):
    return client.post(f"/api/claims/{claim_id}/payment", json={"amount": amount})


def status(client, claim_id="CLM-1001"):
    return client.get(f"/api/claims/{claim_id}").json()["status"]


def sign_off(client, handler_id):
    return client.post("/api/claims/CLM-1001/sign-off", json={"handler_id": handler_id})


def test_approve_under_the_limit_is_decided_and_paid(client):
    assert decide(client, APPROVE)["status"] == "decided"
    response = pay(client, 420.0)
    assert response.status_code == 200
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["decision"]["payout"] == 420.0
    assert claim["payment"] == {"amount": 420.0}


def test_approve_over_the_limit_blocks_the_payment(client):
    assert decide(client, OVER_LIMIT)["status"] == "awaiting_sign_off"
    response = pay(client, 1250.0)
    assert response.status_code == 409
    assert response.json()["detail"] == "Needs a handler's sign-off"
    assert client.get("/api/claims/CLM-1001").json()["payment"] is None


def test_exactly_the_limit_needs_no_sign_off(client):
    assert decide(client, {**APPROVE, "payout": 1000.0})["status"] == "decided"


@pytest.mark.parametrize("decision", [DECLINE, REFER])
def test_cannot_pay_a_declined_or_referred_claim(client, decision):
    decide(client, decision)
    assert pay(client, 100.0).status_code == 409


def test_cannot_pay_an_undecided_claim(client):
    assert pay(client, 100.0).status_code == 409


def test_cannot_pay_twice(client):
    decide(client, APPROVE)
    assert pay(client, 420.0).status_code == 200
    assert pay(client, 420.0).json()["detail"] == "This claim has already been paid"


def test_cannot_pay_a_different_amount(client):
    decide(client, APPROVE)
    assert pay(client, 500.0).status_code == 409


def test_sign_off_needs_a_handler_who_can_approve_over_the_limit(client):
    decide(client, OVER_LIMIT)
    with db.connect() as connection:
        connection.execute(
            "UPDATE handlers SET data = json_set(data, "
            "'$.can_approve_over_limit', json('false')) WHERE handler_id = 'HND-02'"
        )
    assert sign_off(client, "HND-02").status_code == 403
    assert status(client) == "awaiting_sign_off"


def test_sign_off_pays_the_claim(client):
    decide(client, OVER_LIMIT)
    assert sign_off(client, "HND-01").json()["signed_off_by"] == "Dana Whitfield"
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["status"] == "decided"
    assert claim["payment"] == {"amount": 1250.0}
    assert claim["decision"]["signed_off_by"] == "Dana Whitfield"


def test_sign_off_only_when_waiting_for_it(client):
    decide(client, APPROVE)
    assert sign_off(client, "HND-01").status_code == 409


def test_unknown_handler_is_404(client):
    decide(client, OVER_LIMIT)
    assert sign_off(client, "HND-99").status_code == 404


def test_decision_only_while_in_progress(client):
    response = client.post("/api/claims/CLM-1001/decision", json=APPROVE)
    assert response.status_code == 409


def test_decline_with_a_payout_is_rejected(client):
    client.post("/api/claims/CLM-1001/start")
    response = client.post(
        "/api/claims/CLM-1001/decision", json={**DECLINE, "payout": 50}
    )
    assert response.status_code == 422


def test_start_only_a_waiting_claim(client):
    assert client.post("/api/claims/CLM-1001/start").status_code == 200
    assert client.post("/api/claims/CLM-1001/start").status_code == 409


def test_release_puts_the_claim_back(client):
    client.post("/api/claims/CLM-1001/start")
    assert client.post("/api/claims/CLM-1001/release").status_code == 200
    assert status(client) == "waiting"
    assert client.post("/api/claims/CLM-1001/release").status_code == 409


def test_steps_come_back_in_order(client):
    for kind, text in [("tool_call", "get_claim"), ("answer", "Approved $420.00")]:
        response = client.post(
            "/api/claims/CLM-1001/steps", json={"kind": kind, "text": text}
        )
        assert response.status_code == 200
    steps = client.get("/api/claims/CLM-1001/steps").json()
    assert [s["text"] for s in steps] == ["get_claim", "Approved $420.00"]


def test_list_claims_shows_decisions(client):
    decide(client, APPROVE)
    first = client.get("/api/claims").json()[0]
    assert first["status"] == "decided"
    assert first["decision"] == "approve"
    assert first["payout"] == 420.0


def test_seed_script(capsys):
    runpy.run_module("backend.seed", run_name="__main__")
    assert str(db.db_path()) in capsys.readouterr().out
