"""Rebuild the UnderCover database from data/: uv run -m backend.seed"""

from backend.db import db_path, seed

if __name__ == "__main__":
    seed()
    print(f"Seeded {db_path()}")
