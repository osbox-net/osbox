import sqlite3
import sys
from pathlib import Path
import argparse


def enable_wal(db_path: str) -> None:
    db = Path(db_path)

    if not db.exists():
        print(f"Database not found: {db}")
        sys.exit(1)

    conn = sqlite3.connect(str(db), timeout=60)
    try:
        cur = conn.cursor()

        cur.execute("PRAGMA journal_mode=WAL;")
        mode = cur.fetchone()[0]

        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("PRAGMA synchronous;")
        sync = cur.fetchone()[0]

        conn.commit()

        print(f"WAL mode enabled for database: {db}")
        print(f"  journal_mode = {mode}")
        print(f"  synchronous  = {sync}")

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Enable WAL mode for an SQLite database."
    )
    parser.add_argument(
        "db_path",
        help="Path to the SQLite database file.",
    )

    args = parser.parse_args()
    enable_wal(args.db_path)