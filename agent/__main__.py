"""Run the UnderCover Agent on one claim: uv run -m agent CLM-1001"""

import sys
from uuid import uuid4

from agent.main import run

if __name__ == "__main__":
    print(run(sys.argv[1], uuid4().hex))
