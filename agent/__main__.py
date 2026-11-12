"""Run the UnderCover Agent: uv run -m agent [CLM-1001]

With a claim id it decides that claim. Without one it works through every
waiting claim in the queue, one at a time.
"""

import sys
from uuid import uuid4

from agent.main import run, waiting_claims


def work_the_queue() -> None:
    """Decide each waiting claim in turn, carrying on past any that fail."""
    claim_ids = waiting_claims()
    print(f"{len(claim_ids)} claims waiting")
    for number, claim_id in enumerate(claim_ids, start=1):
        print(f"[{number}/{len(claim_ids)}] {claim_id}: ", end="", flush=True)
        try:
            print(run(claim_id, uuid4().hex))
        except Exception as error:
            print(f"stopped: {error}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) > 1:
        sys.exit("Usage: uv run -m agent [CLM-1001]")
    if args:
        print(run(args[0], uuid4().hex))
    else:
        work_the_queue()
