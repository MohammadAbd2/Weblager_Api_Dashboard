import os
import sqlite3

# Dynamically calculate absolute path to ensure database file resolved accurately
# regardless of where the uvicorn execution command was triggered.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "data", "products.db")


def get_conn():
    """Establishes a connection to the SQLite database, ensuring proper dictionary mapping."""
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(DB_PATH)

    # Crucial mapping step: Configures rows to be fetched as dictionary-like objects.
    # Without this row_factory initialization, row_to_dict parser loops will fail (Error 500).
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    """Converts a native SQLite Row object into a standard JSON-serializable Python dictionary."""
    if row is None:
        return {}
    return dict(row)


def insert_record(table: str, payload: dict) -> dict:
    """Dynamic generic helper method to format and insert operational payloads into target tables."""
    if not payload:
        return {}

    fields = list(payload.keys())
    values = list(payload.values())
    placeholders = ", ".join(["?"] * len(fields))

    query = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders}) RETURNING *"

    with get_conn() as conn:
        try:
            cur = conn.execute(query, values)
            row = cur.fetchone()
            conn.commit()
            return row_to_dict(row)
        except sqlite3.Error as e:
            # Verbose logging directly into your server stdout terminal for efficient tracking
            print(f"Database Insert Exception error tracked on table {table}: {e}")
            raise e