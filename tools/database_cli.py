from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sqlite3
import sys
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from database import DB_PATH  # noqa: E402


REQUIRED_TABLES = {
    "users", "students", "courses", "teachers", "groups",
    "group_students", "lessons", "attendance", "payments",
}


def validate_database(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"Database not found: {path}")
    with sqlite3.connect(path) as conn:
        check = conn.execute("PRAGMA quick_check").fetchone()[0]
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    if check != "ok":
        raise ValueError(f"SQLite integrity check failed: {check}")
    missing = REQUIRED_TABLES - tables
    if missing:
        raise ValueError(f"Not an Education Center CRM database; missing: {sorted(missing)}")


def backup_database(source: Path = DB_PATH, destination_dir: Path | None = None) -> Path:
    validate_database(source)
    destination_dir = destination_dir or source.parent / "backups"
    destination_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destination = destination_dir / f"education-crm-{timestamp}.db"
    with sqlite3.connect(source) as source_conn, sqlite3.connect(destination) as target_conn:
        source_conn.backup(target_conn)
    validate_database(destination)
    return destination


def restore_database(source: Path, destination: Path = DB_PATH) -> Path:
    validate_database(source)
    if destination.exists():
        backup_database(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    validate_database(destination)
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backup and restore the Education Center CRM SQLite database.")
    parser.add_argument("--database", type=Path, default=DB_PATH)
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup = subparsers.add_parser("backup", help="Create a validated SQLite backup.")
    backup.add_argument("--destination", type=Path)

    restore = subparsers.add_parser("restore", help="Restore a validated SQLite backup.")
    restore.add_argument("--from", dest="source", type=Path, required=True)
    restore.add_argument("--confirm", action="store_true", help="Confirm replacement of the active database.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "backup":
        result = backup_database(args.database, args.destination)
        print(f"[OK] backup created: {result}")
        return 0
    if not args.confirm:
        print("[ERROR] restore requires --confirm", file=sys.stderr)
        return 2
    result = restore_database(args.source, args.database)
    print(f"[OK] database restored: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
