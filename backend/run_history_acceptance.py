import os
import requests
import time
import subprocess
import sys
import sqlite3
import json

def main():
    print("Starting uvicorn...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
        cwd=os.path.abspath(os.path.dirname(__file__))
    )
    time.sleep(3) # wait for startup
    
    try:
        # GET /scenarios
        print("\n--- Getting Scenarios ---")
        scenarios = requests.get("http://localhost:8001/scenarios").json()
        print(f"Found {len(scenarios)} scenarios.")
        
        # POST each to /analyze
        print("\n--- Analyzing Scenarios ---")
        for s in scenarios:
            r = requests.post("http://localhost:8001/analyze", json=s["payload"]).json()
            print(f"[{s['id']}] case_id: {r['case_id']}, trust_score: {r['trust_score']}, decision: {r['decision']}, challenge_id: {r.get('challenge_id')}")
            
        # GET /history?decision=block
        print("\n--- Filtering History (decision=block) ---")
        h_block = requests.get("http://localhost:8001/history?decision=block").json()
        for item in h_block["items"]:
            print(f"- {item['case_id']}: {item['decision']} (scenario: {item['scenario_id']})")
            
        print("\nStopping server to test persistence...")
    finally:
        proc.terminate()
        proc.wait()
        
    print("Restarting server...")
    proc2 = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
        cwd=os.path.abspath(os.path.dirname(__file__))
    )
    time.sleep(3)
    
    try:
        print("\n--- Checking History Persistence ---")
        h_all = requests.get("http://localhost:8001/history").json()
        print(f"Total history items after restart: {h_all['total']}")
        
        print("\n--- Tampering with Ledger ---")
        from config import DB_PATH
        db_path = DB_PATH
             
        # Python sqlite3 one-liner to edit payload_json
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT seq, payload_json FROM ledger ORDER BY seq ASC LIMIT 1 OFFSET 1").fetchone()
        if row:
            p = json.loads(row[1])
            p["trust_score"] = 999
            conn.execute("UPDATE ledger SET payload_json = ? WHERE seq = ?", (json.dumps(p), row[0]))
            conn.commit()
        conn.close()
        print("Tampering complete.")
        
        print("\n--- Verifying Chain ---")
        v = requests.get("http://localhost:8001/history/verify").json()
        print("Chain Verification:", v)
        
        print("\n--- Resetting History ---")
        requests.delete("http://localhost:8001/history?confirm=true")
        v_reset = requests.get("http://localhost:8001/history/verify").json()
        print("Chain Verification after Reset:", v_reset)
        
    finally:
        proc2.terminate()
        proc2.wait()

if __name__ == "__main__":
    main()
