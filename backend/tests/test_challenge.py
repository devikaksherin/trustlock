import os
import tempfile
import pytest
import time
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

temp_dir = tempfile.TemporaryDirectory()
os.environ["TRUSTLOCK_DATA_DIR"] = temp_dir.name

from backend.main import app
from backend.storage import storage
from backend import challenge

@pytest.fixture(autouse=True)
def setup_db():
    storage.init_db()
    yield

@pytest.fixture(autouse=True)
def mock_video(monkeypatch):
    orig = storage.get_evidence
    def _mock(ev_id):
        if ev_id == "dummy_vid":
            return {"kind": "video", "findings": [{"key": "face_count", "value": 1}]}
        return orig(ev_id)
    monkeypatch.setattr(storage, "get_evidence", _mock)

client = TestClient(app)

# A fake clock
class MockClock:
    def __init__(self):
        self.current = datetime.now(timezone.utc)
    def now(self):
        return self.current
    def advance(self, seconds):
        self.current += timedelta(seconds=seconds)

@pytest.fixture
def mock_now(monkeypatch):
    clock = MockClock()
    monkeypatch.setattr(challenge, "now", clock.now)
    return clock

def test_generate():
    # ALLOW -> 422
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "ALLOW"})
    assert r.status_code == 422
    
    # VERIFY works
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    assert r.status_code == 200
    data = r.json()
    assert "nonce" not in data
    assert "expected_phrase" not in data
    assert data["prototype"] is True
    assert "-" in data["instruction"]
    assert any(c.isdigit() for c in data["instruction"])
    
    # Over 30 generations, > 1 template
    templates = set()
    for _ in range(30):
        r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "BLOCK"})
        templates.add(r.json()["instruction"])
    assert len(templates) > 1

def _get_nonce(challenge_id):
    ch = storage.get_challenge(challenge_id)
    return ch["nonce"]

def test_verify_passes():
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    cid = r.json()["challenge_id"]
    nonce = _get_nonce(cid)
    
    # Exact phrase
    r2 = client.post("/challenge/verify", json={"challenge_id": cid, "response": nonce, "evidence_ids": ["dummy_vid"]})
    assert r2.status_code == 200
    assert r2.json()["status"] == "verified"
    assert r2.json()["final_decision"] == "ALLOW"
    assert r2.json()["checks"] == "full_verification"
    
def test_verify_extra_words():
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    cid = r.json()["challenge_id"]
    nonce = _get_nonce(cid)
    
    resp = f"hello turning right {nonce} ok"
    r2 = client.post("/challenge/verify", json={"challenge_id": cid, "response": resp, "evidence_ids": ["dummy_vid"]})
    assert r2.json()["status"] == "verified"

def test_verify_spoken_digits(monkeypatch):
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    cid = r.json()["challenge_id"]
    
    # Force a known nonce for deterministic testing
    storage.update_challenge(cid, {"nonce": "TRUST-47"})
    
    # "forty seven" -> "47"
    r2 = client.post("/challenge/verify", json={"challenge_id": cid, "response": "trust forty seven", "evidence_ids": ["dummy_vid"]})
    assert r2.json()["status"] == "verified"

def test_retry_and_fail():
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    cid = r.json()["challenge_id"]
    storage.update_challenge(cid, {"nonce": "TRUST-47"})
    
    # "trust 41" -> retry
    r2 = client.post("/challenge/verify", json={"challenge_id": cid, "response": "trust 41", "evidence_ids": ["dummy_vid"]})
    assert r2.json()["status"] == "retry"
    
    # "hello" -> fail
    r3 = client.post("/challenge/verify", json={"challenge_id": cid, "response": "hello", "evidence_ids": ["dummy_vid"]})
    assert r3.json()["status"] == "failed"

def test_empty_response():
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    cid = r.json()["challenge_id"]
    r2 = client.post("/challenge/verify", json={"challenge_id": cid, "response": "", "evidence_ids": ["dummy_vid"]})
    assert r2.json()["status"] == "retry"

def test_attempts():
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    cid = r.json()["challenge_id"]
    storage.update_challenge(cid, {"nonce": "TRUST-47"})
    
    # Retry 1
    r2 = client.post("/challenge/verify", json={"challenge_id": cid, "response": "trust 41", "evidence_ids": ["dummy_vid"]})
    assert r2.json()["attempts_left"] == 2
    
    # Retry 2
    r3 = client.post("/challenge/verify", json={"challenge_id": cid, "response": "trust 41", "evidence_ids": ["dummy_vid"]})
    assert r3.json()["attempts_left"] == 1
    
    # Retry 3 -> exhausted
    r4 = client.post("/challenge/verify", json={"challenge_id": cid, "response": "trust 41", "evidence_ids": ["dummy_vid"]})
    assert r4.json()["status"] == "failed"
    assert r4.json()["reason"] == "attempts_exhausted"

def test_expiry(mock_now):
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    cid = r.json()["challenge_id"]
    
    mock_now.advance(91)
    
    r2 = client.post("/challenge/verify", json={"challenge_id": cid, "response": "trust 47", "evidence_ids": ["dummy_vid"]})
    assert r2.json()["status"] == "failed"
    assert r2.json()["reason"] == "expired"

def test_single_use():
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    cid = r.json()["challenge_id"]
    storage.update_challenge(cid, {"nonce": "TRUST-47"})
    
    client.post("/challenge/verify", json={"challenge_id": cid, "response": "trust 47", "evidence_ids": ["dummy_vid"]})
    
    # Second verify
    r2 = client.post("/challenge/verify", json={"challenge_id": cid, "response": "trust 47", "evidence_ids": ["dummy_vid"]})
    assert r2.status_code == 409

def test_simulation():
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    cid = r.json()["challenge_id"]
    
    r2 = client.post("/challenge/verify", json={"challenge_id": cid, "simulation": True, "evidence_ids": ["dummy_vid"]})
    assert r2.status_code == 422
    
    r3 = client.post("/challenge/verify", json={"challenge_id": cid, "simulation": True, "simulated_outcome": "unclear", "evidence_ids": ["dummy_vid"]})
    assert r3.json()["status"] == "retry"

def test_final_decisions():
    # VERIFY + failed -> BLOCK
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    r2 = client.post("/challenge/verify", json={"challenge_id": r.json()["challenge_id"], "simulation": True, "simulated_outcome": "fail", "evidence_ids": ["dummy_vid"]})
    assert r2.json()["final_decision"] == "BLOCK"
    
    # BLOCK + verified -> BLOCK, human_review True
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "BLOCK"})
    r2 = client.post("/challenge/verify", json={"challenge_id": r.json()["challenge_id"], "simulation": True, "simulated_outcome": "pass", "evidence_ids": ["dummy_vid"]})
    assert r2.json()["final_decision"] == "BLOCK"
    assert r2.json()["human_review"] is True
    
    # BLOCK + failed -> BLOCK
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "BLOCK"})
    r2 = client.post("/challenge/verify", json={"challenge_id": r.json()["challenge_id"], "simulation": True, "simulated_outcome": "fail", "evidence_ids": ["dummy_vid"]})
    assert r2.json()["final_decision"] == "BLOCK"
    assert r2.json()["human_review"] is False

def test_get_challenge_view(mock_now):
    r = client.post("/challenge/generate", json={"case_id": "c1", "decision": "VERIFY"})
    cid = r.json()["challenge_id"]
    
    view_res = client.get(f"/challenge/{cid}")
    assert view_res.status_code == 200
    data = view_res.json()
    assert data["challenge_id"] == cid
    assert data["status"] == "pending"
    assert "remaining_seconds" in data
    assert "nonce" not in data
    assert "expected_phrase" not in data
    assert data["expired"] is False
    
    mock_now.advance(91)
    
    view_res2 = client.get(f"/challenge/{cid}")
    data2 = view_res2.json()
    assert data2["remaining_seconds"] == 0
    assert data2["expired"] is True
    assert data2["status"] == "pending" # Still pending, GET doesn't mutate state
