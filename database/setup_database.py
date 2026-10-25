from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / "database"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "buildback.db"
SCHEMA = DB_DIR / "schema.sql"

with sqlite3.connect(DB_PATH) as connection:
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()

print(f"Database ready: {DB_PATH}")
print("Tables:")
for (table,) in tables:
    print(f" - {table}")
