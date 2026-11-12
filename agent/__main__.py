"""Run the UnderCover Agent on one claim: uv run -m agent CLM-1001"""

import sys
from uuid import uuid4

from agent.main import run

if __name__ == "__main__":
    claim_ids = sys.argv[1:]
    if len(claim_ids) != 1:
        sys.exit("Usage: uv run -m agent CLM-1001")
    print(run(claim_ids[0], uuid4().hex))
