import os
import requests
import time
import subprocess
import sys

def main():
    print("Starting uvicorn...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
        cwd=os.path.abspath(os.path.dirname(__file__))
    )
    time.sleep(3) # wait for startup
    
    try:
        print("\n--- a) Generate BLOCK, verify simulation fail ---")
        r1 = requests.post("http://localhost:8001/challenge/generate", json={"case_id": "c1", "decision": "BLOCK"}).json()
        print("Generate:", r1)
        r2 = requests.post("http://localhost:8001/challenge/verify", json={"challenge_id": r1["challenge_id"], "simulation": True, "simulated_outcome": "fail"}).json()
        print("Verify:", r2)
        
        print("\n--- b) Generate VERIFY, verify simulation pass ---")
        r3 = requests.post("http://localhost:8001/challenge/generate", json={"case_id": "c2", "decision": "VERIFY"}).json()
        print("Generate:", r3)
        r4 = requests.post("http://localhost:8001/challenge/verify", json={"challenge_id": r3["challenge_id"], "simulation": True, "simulated_outcome": "pass"}).json()
        print("Verify:", r4)
        
        print("\n--- c) Generate VERIFY, live verify matching nonce ---")
        r5 = requests.post("http://localhost:8001/challenge/generate", json={"case_id": "c3", "decision": "VERIFY"}).json()
        print("Generate:", r5)
        # instruction is something like: Look at the camera and say TRUST-47 clearly.
        import re
        m = re.search(r'([A-Z]+-\d+)', r5["instruction"])
        nonce = m.group(1) if m else ""
        print("Extracted nonce:", nonce)
        r6 = requests.post("http://localhost:8001/challenge/verify", json={"challenge_id": r5["challenge_id"], "response": nonce}).json()
        print("Verify:", r6)
        
        print("\n--- d) Verify same challenge again (expect 409) ---")
        r7 = requests.post("http://localhost:8001/challenge/verify", json={"challenge_id": r5["challenge_id"], "response": nonce})
        print("Status code:", r7.status_code)
        print("Response:", r7.json())
        
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
