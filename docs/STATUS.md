# Status

The claims pilot from `docs/PLAN.md` is built.

## Built

- `backend/`: FastAPI on SQLite (`backend/db.py`). The database is seeded from `data/` on first start, leaving out `data/evals/` and `data/security/`. Operations to read claims, policies, claim history, the policy wording, the agent's instructions (`backend/instructions.md`) and the handlers; to start, release and decide a claim; to pay it; for a handler to sign off a payout over $1,000; for the agent's activity steps; and to start the agent on a claim in the background. A payment over $1,000 is refused until a handler signs off, whatever the agent does.
- `agent/`: the UnderCover Agent, `run(claim_id, thread_id)`, on LangChain's `create_agent`. It starts the claim, takes its instructions from the backend, reads the claim, policy, claim history and policy wording through the API, records its decision and tries to pay. Middleware logs each tool call and result as a step; a failed run logs an error and puts the claim back in the queue.
- `dashboard/`: React in UnderCover's brand, light and dark. The queue (`#/`) with counts by state and a "Run agent" button on each waiting claim; the claim page (`#/claims/CLM-1001`) with the claim in full, the decision and payment, a handler's sign-off for payouts over $1,000, and the agent's steps refreshed every second until its run finishes; and the agent's instructions, read only (`#/instructions`). Code is in domain folders: `queue/`, `claim/`, `instructions/`, `shell/`, `ui/` and `lib/`.
- `e2e/`: Playwright tests of the queue, a claim in full, a decision, the over-limit sign-off and the instructions. They run on their own backend (port 8001), dashboard (port 5174) and freshly seeded `backend/e2e.db`, and never call a model.

## Running it

- `npm run dev` starts the backend on port 8000 and the dashboard on http://localhost:5173. Open a claim and press "Run agent" to watch the agent decide it.
- `uv run -m backend.seed` resets the database (`backend/undercover.db`) to the 25 waiting claims. Set `UNDERCOVER_DB` to use another file.
- `uv run -m agent CLM-1001` runs the agent on one claim from the command line, with the backend running. `uv run -m agent` on its own works through every waiting claim, one at a time, printing each result and carrying on past any run that fails; each claim's steps show live in the dashboard. `UNDERCOVER_BACKEND_URL` sets where it finds the backend (default `http://localhost:8000`) and `MODEL_NAME` the model (default `openai/gpt-6-luna`; `openrouter/free` is free).
- `npm run check` runs every check.

## Notes

- The agent works from the policy wording alone, as the spec asks, so claims that need the claims manual or judgment on the customer's history may not match the handlers' decisions. Scoring against `data/evals/` comes with the evaluations build.
- Live runs during the build: CLM-1001 (trip delay, approved $420), CLM-1004 (baggage delay, $186), CLM-1005 (passport, $243) and CLM-1006 (emergency medical, $425), each decided with a reason and a section and paid.
