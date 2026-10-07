import httpx
import sys

def main():
    print("Generating demo assets...")
    
    payload = {
        "identity": {
            "claimed_name": "Alice Smith",
            "claimed_role": "user",
            "credential_verified": True,
            "face_match": 40,
            "voice_match": 40,
            "liveness_ok": False,
            "document_tampered": False
        },
        "context": {
            "known_device": False,
            "location_matches_pattern": False,
            "remote_access_tool": True,
            "local_hour": 2
        },
        "behavior": {
            "urgency": "critical",
            "pressure_language": True,
            "skipped_verification_steps": True,
            "unusual_session_behavior": True
        },
        "transaction": {
            "action_type": "fund_transfer",
            "amount_inr": 1500000,
            "usual_amount_inr": 5000,
            "recipient_label": "Unknown",
            "new_recipient": True,
            "recipient_account_age_days": 1,
            "tx_last_hour": 5
        },
        "evidence_ids": []
    }
    
    try:
        with httpx.Client(base_url="http://localhost:8001") as client:
            res = client.post("/analyze", json=payload)
            res.raise_for_status()
            data = res.json()
            decision = data.get("decision")
            print(f"Analyze decision: {decision}")
            
            if decision not in ("VERIFY", "BLOCK"):
                print("Failed: Expected VERIFY or BLOCK to trigger a challenge.")
                sys.exit(1)
                
            challenge_id = data.get("challenge_id")
            if not challenge_id:
                print("Failed: No challenge_id returned.")
                sys.exit(1)
                
            print(f"Challenge started: {challenge_id}")
            
            verify_payload = {
                "challenge_id": challenge_id,
                "simulation": True,
                "simulated_outcome": "pass"
            }
            res = client.post("/challenge/verify", json=verify_payload)
            res.raise_for_status()
            verify_data = res.json()
            print(f"Verify outcome: {verify_data.get('status')}")
            
            res = client.get("/history")
            res.raise_for_status()
            history = res.json().get("items", [])
            
            found = any(i.get("challenge_id") == challenge_id for i in history)
            if not found:
                print("Failed: Challenge not found in history.")
                sys.exit(1)
                
            print("DEMO ASSETS GENERATED SUCCESS")
    except httpx.HTTPStatusError as e:
        print(f"HTTP Failed with error: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
