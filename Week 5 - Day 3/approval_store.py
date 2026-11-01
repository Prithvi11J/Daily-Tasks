"""Local prototype PAM request register. Never grants real access."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DB_PATH = Path(__file__).with_name('runtime_data') / 'pam_approvals.sqlite3'

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('''CREATE TABLE IF NOT EXISTS requests (
        id TEXT PRIMARY KEY, requested_at TEXT NOT NULL,
        description TEXT NOT NULL, status TEXT NOT NULL,
        decided_at TEXT, reviewer_note TEXT NOT NULL DEFAULT ''
    )''')
    db.commit()
    return db

def create_request(description: str) -> str:
    request_id = str(uuid4())
    with connect() as db:
        db.execute('INSERT INTO requests (id, requested_at, description, status) VALUES (?, ?, ?, ?)',
                   (request_id, datetime.now(timezone.utc).isoformat(), description[:1500], 'PENDING'))
    return request_id

def get_request(request_id: str):
    with connect() as db:
        row = db.execute('SELECT * FROM requests WHERE id=?', (request_id,)).fetchone()
        return dict(row) if row else None

def list_requests():
    with connect() as db:
        return [dict(row) for row in db.execute('SELECT * FROM requests ORDER BY requested_at DESC LIMIT 100')]

def decide_request(request_id: str, decision: str, note: str) -> bool:
    if decision not in ('APPROVED', 'REJECTED'):
        raise ValueError('Invalid decision')
    with connect() as db:
        updated = db.execute(
            "UPDATE requests SET status=?, decided_at=?, reviewer_note=? WHERE id=? AND status='PENDING'",
            (decision, datetime.now(timezone.utc).isoformat(), note[:500], request_id)
        )
        return updated.rowcount == 1

# Understand the Important Code
# SQLite persists demo request statuses across Streamlit reruns and restarts.
# The status transition is allowed only once, from PENDING to APPROVED/REJECTED.
# Important Notes
# This is not an access management system; no access or tickets are created.
# Never store passwords, tokens, secrets or genuine employee data here.
