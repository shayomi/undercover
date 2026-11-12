# Status

The claims pilot from `docs/PLAN.md`, in progress.

## Built

- `backend/`: FastAPI on SQLite (`backend/db.py`). The database is seeded from `data/` on first start, leaving out `data/evals/` and `data/security/`. Operations to read claims, policies, claim history, the policy wording, the agent's instructions (`backend/instructions.md`) and the handlers; to start, release and decide a claim; to pay it; for a handler to sign off a payout over $1,000; and for the agent's activity steps. A payment over $1,000 is refused until a handler signs off.
- `agent/`: the UnderCover Agent, `run(claim_id, thread_id)`. It starts the claim, takes its instructions from the backend, reads the claim, policy, claim history and policy wording through the API, records its decision and tries to pay. Each tool call and result is logged as a step; a failed run logs an error and puts the claim back in the queue. `run_agent` in the backend starts it in the background.
- `dashboard/`: still the one-page health check.
- `e2e/`: one test of that page.

## Running it

- `uv run -m backend.seed` rebuilds the database (`backend/undercover.db`). Set `UNDERCOVER_DB` to use another file.
- `uv run -m agent CLM-1001` runs the agent on one claim; the backend must be running. `UNDERCOVER_BACKEND_URL` sets where the agent finds the backend (default `http://localhost:8000`), and `MODEL_NAME` the model.
- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173.
- `npm run check` runs every check.
