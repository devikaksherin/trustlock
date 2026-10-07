import sqlite3
import json
import hashlib
import threading
from datetime import datetime, timezone
from .config import DB_PATH

GENESIS_HASH = "0" * 64
ledger_lock = threading.RLock()

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

class SqliteStorage:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    original_name TEXT,
                    stored_name TEXT,
                    kind TEXT,
                    mime TEXT,
                    ext TEXT,
                    size_bytes INTEGER,
                    sha256 TEXT,
                    uploaded_at TEXT,
                    findings_json TEXT,
                    notes_json TEXT,
                    extracted_text TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS challenges (
                    id TEXT PRIMARY KEY,
                    case_id TEXT,
                    original_decision TEXT,
                    type TEXT,
                    instruction TEXT,
                    nonce TEXT,
                    status TEXT,
                    attempts_left INTEGER,
                    created_at TEXT,
                    expires_at TEXT,
                    resolved_at TEXT,
                    last_outcome TEXT,
                    final_decision TEXT,
                    final_note TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ledger (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    case_id TEXT,
                    payload_json TEXT,
                    prev_hash TEXT,
                    record_hash TEXT,
                    created_at TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_ledger_case_id ON ledger(case_id)')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trust_profiles (
                    id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                )
            ''')
            conn.commit()

    def save_evidence(self, record: dict):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO evidence (
                    id, original_name, stored_name, kind, mime, ext, size_bytes,
                    sha256, uploaded_at, findings_json, notes_json, extracted_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record['id'],
                record['original_name'],
                record['stored_name'],
                record['kind'],
                record['mime'],
                record['ext'],
                record['size_bytes'],
                record['sha256'],
                record['uploaded_at'],
                json.dumps(record.get('findings', [])),
                json.dumps(record.get('notes', [])),
                record.get('extracted_text')
            ))
            conn.commit()

    def get_evidence(self, id: str):
        with self.get_connection() as conn:
            row = conn.execute('SELECT * FROM evidence WHERE id = ?', (id,)).fetchone()
            if row:
                res = dict(row)
                res['findings'] = json.loads(res.get('findings_json') or '[]')
                res['notes'] = json.loads(res.get('notes_json') or '[]')
                return res
            return None

    def delete_evidence(self, id: str):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM evidence WHERE id = ?', (id,))
            conn.commit()

    def save_challenge(self, record: dict):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO challenges (
                    id, case_id, original_decision, type, instruction, nonce,
                    status, attempts_left, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record['id'],
                record['case_id'],
                record['original_decision'],
                record['type'],
                record['instruction'],
                record['nonce'],
                record['status'],
                record['attempts_left'],
                record['created_at'],
                record['expires_at']
            ))
            conn.commit()

    def get_challenge(self, id: str):
        with self.get_connection() as conn:
            row = conn.execute('SELECT * FROM challenges WHERE id = ?', (id,)).fetchone()
            return dict(row) if row else None

    def update_challenge(self, id: str, updates: dict):
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values())
        values.append(id)
        with self.get_connection() as conn:
            conn.execute(f'UPDATE challenges SET {set_clause} WHERE id = ?', values)
            conn.commit()

    def append_event(self, event_type: str, case_id: str, payload: dict):
        with ledger_lock:
            with self.get_connection() as conn:
                conn.execute('BEGIN IMMEDIATE')
                
                row = conn.execute('SELECT record_hash FROM ledger ORDER BY seq DESC LIMIT 1').fetchone()
                prev_hash = row['record_hash'] if row else GENESIS_HASH
                
                created_at = datetime.now(timezone.utc).isoformat()
                
                # put inside payload
                payload["event_type"] = event_type
                payload["case_id"] = case_id
                payload["created_at"] = created_at
                
                payload_json = canonical_json(payload)
                record_hash = hashlib.sha256((prev_hash + payload_json).encode('utf-8')).hexdigest()
                
                cur = conn.execute('''
                    INSERT INTO ledger (event_type, case_id, payload_json, prev_hash, record_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (event_type, case_id, payload_json, prev_hash, record_hash, created_at))
                
                conn.commit()
                return cur.lastrowid

    def next_case_id(self):
        with ledger_lock:
            with self.get_connection() as conn:
                row = conn.execute("SELECT COUNT(*) as c FROM ledger WHERE event_type = 'ANALYSIS'").fetchone()
                count = row['c'] + 1 if row else 1
                yr = datetime.now(timezone.utc).year
                return f"TL-{yr}-{count:06d}"

    def verify_chain(self):
        # Tamper-EVIDENT, not tamper-proof. Deleting the newest rows cannot be detected by the chain alone,
        # so the UI shows head_hash for comparison. Production would anchor it externally.
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM ledger ORDER BY seq ASC").fetchall()
            
        if not rows:
            return {"valid": True, "length": 0, "head_hash": None, "broken_at": None, "reason": None}
            
        expected_prev = GENESIS_HASH
        
        for row in rows:
            seq = row["seq"]
            
            # Check prev_hash
            if row["prev_hash"] != expected_prev:
                return {"valid": False, "length": len(rows), "head_hash": None, "broken_at": seq, "reason": "link_broken"}
                
            # Check JSON parse
            try:
                payload = json.loads(row["payload_json"])
            except json.JSONDecodeError:
                return {"valid": False, "length": len(rows), "head_hash": None, "broken_at": seq, "reason": "bad_json"}
                
            # Check columns vs payload
            if payload.get("event_type") != row["event_type"] or \
               payload.get("case_id") != row["case_id"] or \
               payload.get("created_at") != row["created_at"]:
                return {"valid": False, "length": len(rows), "head_hash": None, "broken_at": seq, "reason": "column_mismatch"}
                
            # Check hash
            h = hashlib.sha256((expected_prev + row["payload_json"]).encode("utf-8")).hexdigest()
            if h != row["record_hash"]:
                return {"valid": False, "length": len(rows), "head_hash": None, "broken_at": seq, "reason": "hash_mismatch"}
                
            expected_prev = row["record_hash"]
            
        return {"valid": True, "length": len(rows), "head_hash": expected_prev, "broken_at": None, "reason": None}

    def reset_ledger(self):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM ledger")
            conn.execute("DELETE FROM challenges")
            conn.execute("DELETE FROM trust_profiles")
            conn.commit()
            
    def list_cases(self, decision_filter=None, limit=50, offset=0):
        with self.get_connection() as conn:
            if decision_filter and decision_filter.lower() != "all":
                q = "SELECT * FROM ledger WHERE event_type = 'ANALYSIS' AND json_extract(payload_json, '$.decision') = ? ORDER BY seq DESC LIMIT ? OFFSET ?"
                rows = conn.execute(q, (decision_filter.upper(), limit, offset)).fetchall()
                count_q = "SELECT COUNT(*) as c FROM ledger WHERE event_type = 'ANALYSIS' AND json_extract(payload_json, '$.decision') = ?"
                total = conn.execute(count_q, (decision_filter.upper(),)).fetchone()['c']
            else:
                q = "SELECT * FROM ledger WHERE event_type = 'ANALYSIS' ORDER BY seq DESC LIMIT ? OFFSET ?"
                rows = conn.execute(q, (limit, offset)).fetchall()
                count_q = "SELECT COUNT(*) as c FROM ledger WHERE event_type = 'ANALYSIS'"
                total = conn.execute(count_q).fetchone()['c']
                
            return [dict(r) for r in rows], total

    def get_case(self, case_id: str):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM ledger WHERE case_id = ? ORDER BY seq ASC", (case_id,)).fetchall()
            return [dict(r) for r in rows]

    def save_profile(self, profile: dict):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO trust_profiles (
                    id, payload_json
                ) VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET payload_json=excluded.payload_json
            ''', (profile['id'], json.dumps(profile)))
            conn.commit()

    def get_profile(self, profile_id: str):
        with self.get_connection() as conn:
            row = conn.execute('SELECT payload_json FROM trust_profiles WHERE id = ?', (profile_id,)).fetchone()
            return json.loads(row['payload_json']) if row else None

    def list_profiles(self):
        with self.get_connection() as conn:
            rows = conn.execute('SELECT payload_json FROM trust_profiles').fetchall()
            return [json.loads(r['payload_json']) for r in rows]

    def delete_profile(self, profile_id: str):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM trust_profiles WHERE id = ?', (profile_id,))
            conn.commit()

storage = SqliteStorage()
