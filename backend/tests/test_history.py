import os
import tempfile
import pytest
import concurrent.futures
from fastapi.testclient import TestClient

temp_dir = tempfile.TemporaryDirectory()
os.environ["TRUSTLOCK_DATA_DIR"] = temp_dir.name

from backend.main import app
from backend.storage import storage, SqliteStorage
from backend.scenarios import SCENARIOS
import json
import sqlite3
import hashlib

@pytest.fixture(autouse=True)
def setup_db():
    storage.init_db()
    # Reset ledger before each test
    storage.reset_ledger()
    yield

client = TestClient(app)

def test_analyze_and_persistence():
    # Analyze
    scen = SCENARIOS[0]
    r = client.post("/analyze", json=scen["payload"])
    assert r.status_code == 200
    
    # New storage instance
    st = SqliteStorage()
    cases, total = st.list_cases()
    assert total == 1
    assert cases[0]["case_id"].startswith("TL-")

def test_concurrency():
    scen = SCENARIOS[0]
    
    def run_analyze():
        resp = client.post("/analyze", json=scen["payload"])
        return resp.json()["case_id"]
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_analyze) for _ in range(20)]
        ids = [f.result() for f in concurrent.futures.as_completed(futures)]
        
    assert len(set(ids)) == 20
    
    verify = storage.verify_chain()
    assert verify["valid"] is True
    assert verify["length"] == 20

def test_chain_breakage():
    # Generate 3 analyses
    client.post("/analyze", json=SCENARIOS[0]["payload"])
    client.post("/analyze", json=SCENARIOS[1]["payload"])
    client.post("/analyze", json=SCENARIOS[2]["payload"])
    
    assert storage.verify_chain()["valid"] is True
    
    # Hash mismatch
    with storage.get_connection() as conn:
        row = conn.execute("SELECT seq, payload_json FROM ledger ORDER BY seq ASC LIMIT 1 OFFSET 1").fetchone()
        payload = json.loads(row["payload_json"])
        payload["trust_score"] = 999
        conn.execute("UPDATE ledger SET payload_json = ? WHERE seq = ?", (json.dumps(payload), row["seq"]))
        conn.commit()
        
    verify = storage.verify_chain()
    assert verify["valid"] is False
    assert verify["broken_at"] == row["seq"]
    assert verify["reason"] == "hash_mismatch"
    
    # Revert
    storage.reset_ledger()
    client.post("/analyze", json=SCENARIOS[0]["payload"])
    client.post("/analyze", json=SCENARIOS[1]["payload"])
    client.post("/analyze", json=SCENARIOS[2]["payload"])
    
    # Delete middle row
    with storage.get_connection() as conn:
        conn.execute("DELETE FROM ledger WHERE seq = (SELECT seq FROM ledger ORDER BY seq ASC LIMIT 1 OFFSET 1)")
        conn.commit()
        
    verify = storage.verify_chain()
    assert verify["valid"] is False
    assert verify["reason"] == "link_broken"
    
    # Revert
    storage.reset_ledger()
    client.post("/analyze", json=SCENARIOS[0]["payload"])
    
    # Column mismatch
    with storage.get_connection() as conn:
        conn.execute("UPDATE ledger SET case_id = 'FAKE' WHERE seq = (SELECT seq FROM ledger LIMIT 1)")
        conn.commit()
        
    verify = storage.verify_chain()
    assert verify["valid"] is False
    assert verify["reason"] == "column_mismatch"

def test_challenge_events_and_effective_decision():
    # VERIFY scenario
    r = client.post("/analyze", json=SCENARIOS[1]["payload"])
    cid = r.json()["challenge_id"]
    
    # Retry -> appends none
    client.post("/challenge/verify", json={"challenge_id": cid, "simulation": True, "simulated_outcome": "unclear"})
    v = storage.verify_chain()
    assert v["length"] == 1 # Just the ANALYSIS event
    
    # Pass -> appends CHALLENGE_RESULT
    client.post("/challenge/verify", json={"challenge_id": cid, "simulation": True, "simulated_outcome": "pass"})
    v2 = storage.verify_chain()
    assert v2["length"] == 2
    
    # Check effective decision in history
    h = client.get("/history").json()
    item = h["items"][0]
    assert item["effective_decision"] == "ALLOW"
    
    storage.reset_ledger()
    
    # BLOCK scenario
    r = client.post("/analyze", json=SCENARIOS[2]["payload"])
    cid = r.json()["challenge_id"]
    
    # Pass -> BLOCK + human_review
    client.post("/challenge/verify", json={"challenge_id": cid, "simulation": True, "simulated_outcome": "pass"})
    h = client.get("/history").json()
    item = h["items"][0]
    assert item["effective_decision"] == "BLOCK"
    assert item["challenge"]["human_review"] is True

def test_api_scenarios():
    # ALLOW scenario
    r = client.post("/analyze", json=SCENARIOS[0]["payload"])
    assert r.json()["challenge_id"] is None
    
    # VERIFY scenario
    r = client.post("/analyze", json=SCENARIOS[1]["payload"])
    assert r.json()["challenge_id"] is not None
    
    # Forged credential scenario mentions policy
    r = client.post("/analyze", json=SCENARIOS[3]["payload"])
    assert "Blocked by policy" in r.json()["summary"]
    
def test_paging_filtering():
    client.post("/analyze", json=SCENARIOS[0]["payload"]) # ALLOW
    client.post("/analyze", json=SCENARIOS[1]["payload"]) # VERIFY
    client.post("/analyze", json=SCENARIOS[2]["payload"]) # BLOCK
    client.post("/analyze", json=SCENARIOS[3]["payload"]) # BLOCK
    
    r_all = client.get("/history").json()
    assert r_all["total"] == 4
    
    r_allow = client.get("/history?decision=allow").json()
    assert r_allow["total"] == 1
    
    r_block = client.get("/history?decision=block").json()
    assert r_block["total"] == 2

def test_delete_history():
    client.post("/analyze", json=SCENARIOS[0]["payload"])
    
    r = client.delete("/history")
    assert r.status_code == 400
    
    r2 = client.delete("/history?confirm=true")
    assert r2.status_code == 204
    
    assert storage.verify_chain()["length"] == 0

def test_invalid_body():
    r = client.post("/analyze", json={"foo": "bar"})
    assert r.status_code == 422
    assert "detail" in r.json()
