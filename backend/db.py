"""The UnderCover database: SQLite, seeded from data/."""

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DEFAULT_DB = ROOT / "backend" / "undercover.db"

SCHEMA = """
CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    status TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE TABLE policies (policy_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE customers (customer_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE plans (plan TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE add_ons (add_on TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE handlers (handler_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE decisions (
    claim_id TEXT PRIMARY KEY,
    decision TEXT NOT NULL,
    payout REAL NOT NULL,
    reason TEXT NOT NULL,
    policy_section TEXT NOT NULL,
    signed_off_by TEXT
);
CREATE TABLE payments (claim_id TEXT PRIMARY KEY, amount REAL NOT NULL);
CREATE TABLE steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL
);
"""


def db_path() -> Path:
    """Return the database file, from UNDERCOVER_DB or the default."""
    return Path(os.getenv("UNDERCOVER_DB") or DEFAULT_DB)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, and close it."""
    connection = sqlite3.connect(db_path())
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def load(name: str) -> list[dict]:
    """Load one JSON file of records from data/."""
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def rows(items: list[dict], key: str) -> list[tuple[str, str]]:
    """Pair each record with its id, ready to insert."""
    return [(item[key], json.dumps(item)) for item in items]


def seed() -> None:
    """Rebuild the database from data/, leaving out evals/ and security/."""
    path = db_path()
    path.unlink(missing_ok=True)
    claims = load("claims.json")
    plans = json.loads((DATA / "plans.json").read_text(encoding="utf-8"))
    company = (DATA / "company.json").read_text(encoding="utf-8")
    wording = (DATA / "policy_wording.md").read_text(encoding="utf-8")
    with connect() as connection:
        connection.executescript(SCHEMA)
        connection.executemany(
            "INSERT INTO claims VALUES (?, ?, ?, 'waiting', ?)",
            [
                (c["claim_id"], c["policy_id"], c["customer_id"], json.dumps(c))
                for c in claims
            ],
        )
        connection.executemany(
            "INSERT INTO policies VALUES (?, ?)",
            rows(load("policies.json"), "policy_id"),
        )
        connection.executemany(
            "INSERT INTO customers VALUES (?, ?)",
            rows(load("customers.json"), "customer_id"),
        )
        connection.executemany(
            "INSERT INTO plans VALUES (?, ?)", rows(plans["plans"], "plan")
        )
        connection.executemany(
            "INSERT INTO add_ons VALUES (?, ?)", rows(plans["add_ons"], "add_on")
        )
        connection.executemany(
            "INSERT INTO handlers VALUES (?, ?)",
            rows(load("handlers.json"), "handler_id"),
        )
        connection.executemany(
            "INSERT INTO settings VALUES (?, ?)",
            [
                ("company", company),
                ("deductible_applies_to", json.dumps(plans["deductible_applies_to"])),
                ("policy_wording", json.dumps(wording)),
            ],
        )


def ensure_seeded() -> None:
    """Seed the database if it doesn't exist yet."""
    if not db_path().exists():
        seed()
