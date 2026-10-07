SCENARIOS = [
    {
        "id": "routine-supply-payment",
        "title": "Routine supply payment",
        "narrative": "A known officer approves a small payment to an existing vendor for rescue supplies, from a known device at a usual location.",
        "expected_decision": "ALLOW",
        "featured": False,
        "payload": {
            "profile_id": "alice_001",
            "identity": {
                "claimed_name": "Officer R. Menon",
                "claimed_role": "District Fire Officer",
                "credential_verified": True,
                "face_match": 92,
                "voice_match": 90,
                "liveness_ok": True,
                "document_tampered": False,
                "sources": {
                    "face_match": "simulated",
                    "voice_match": "simulated",
                    "liveness_ok": "simulated",
                    "document_tampered": "simulated"
                }
            },
            "context": {
                "device_label": "iPhone 13",
                "location_label": "Bangalore",
                "known_device": True,
                "location_matches_pattern": True,
                "remote_access_tool": False,
                "local_hour": 11,
                "sources": {
                    "known_device": "simulated",
                    "location_matches_pattern": "simulated",
                    "remote_access_tool": "simulated",
                    "local_hour": "simulated"
                }
            },
            "behavior": {
                "urgency": "low",
                "pressure_language": False,
                "skipped_verification_steps": False,
                "unusual_session_behavior": False,
                "sources": {
                    "urgency": "simulated",
                    "pressure_language": "simulated",
                    "skipped_verification_steps": "simulated",
                    "unusual_session_behavior": "simulated"
                }
            },
            "transaction": {
                "action_type": "fund_transfer",
                "amount_inr": 4500,
                "usual_amount_inr": 5000,
                "recipient_label": "Rent",
                "new_recipient": False,
                "recipient_account_age_days": 900,
                "tx_last_hour": 0,
                "sources": {
                    "action_type": "simulated",
                    "amount_inr": "simulated",
                    "usual_amount_inr": "simulated",
                    "recipient_label": "simulated",
                    "new_recipient": "simulated",
                    "recipient_account_age_days": "simulated",
                    "tx_last_hour": "simulated"
                }
            },
            "evidence_ids": []
        }
    },
    {
        "id": "overnight-vendor-payment",
        "title": "Overnight Vendor Payment",
        "narrative": "Admin Bob makes a large payment at 2 AM from a new device in Delhi.",
        "expected_decision": "VERIFY",
        "featured": False,
        "payload": {
            "profile_id": "bob_002",
            "identity": {
                "claimed_name": "Unknown",
                "claimed_role": "User",
                "credential_verified": False,
                "face_match": 85,
                "voice_match": 84,
                "liveness_ok": True,
                "document_tampered": False,
                "sources": {
                    "face_match": "simulated",
                    "voice_match": "simulated",
                    "liveness_ok": "simulated",
                    "document_tampered": "simulated"
                }
            },
            "context": {
                "device_label": "Windows PC",
                "location_label": "Delhi",
                "known_device": False,
                "location_matches_pattern": False,
                "remote_access_tool": False,
                "local_hour": 2,
                "sources": {
                    "known_device": "simulated",
                    "location_matches_pattern": "simulated",
                    "remote_access_tool": "simulated",
                    "local_hour": "simulated"
                }
            },
            "behavior": {
                "urgency": "medium",
                "pressure_language": False,
                "skipped_verification_steps": False,
                "unusual_session_behavior": False,
                "sources": {
                    "urgency": "simulated",
                    "pressure_language": "simulated",
                    "skipped_verification_steps": "simulated",
                    "unusual_session_behavior": "simulated"
                }
            },
            "transaction": {
                "action_type": "fund_transfer",
                "amount_inr": 250000,
                "usual_amount_inr": 50000,
                "recipient_label": "Vendor Payment",
                "new_recipient": True,
                "recipient_account_age_days": None,
                "tx_last_hour": 0,
                "sources": {
                    "action_type": "simulated",
                    "amount_inr": "simulated",
                    "usual_amount_inr": "simulated",
                    "recipient_label": "simulated",
                    "new_recipient": "simulated",
                    "recipient_account_age_days": "simulated",
                    "tx_last_hour": "simulated"
                }
            },
            "evidence_ids": []
        }
    },
    {
        "id": "flood-emergency-cloned-officer",
        "title": "Flood emergency: AI-cloned officer",
        "narrative": "During a flood a firefighter gets a live video call from what looks and sounds like the district emergency officer demanding an urgent ₹2,00,000 transfer to a new account for 'resource redirection'. Face and voice look genuine (simulated); the request is not.",
        "expected_decision": "BLOCK",
        "featured": True,
        "payload": {
            "identity": {
                "claimed_name": "Officer",
                "claimed_role": "Officer",
                "credential_verified": False,
                "face_match": 88,
                "voice_match": 86,
                "liveness_ok": True,
                "document_tampered": False,
                "sources": {
                    "face_match": "simulated",
                    "voice_match": "simulated",
                    "liveness_ok": "simulated",
                    "document_tampered": "simulated"
                }
            },
            "context": {
                "known_device": False,
                "location_matches_pattern": False,
                "remote_access_tool": False,
                "local_hour": 2,
                "sources": {
                    "known_device": "simulated",
                    "location_matches_pattern": "simulated",
                    "remote_access_tool": "simulated",
                    "local_hour": "simulated"
                }
            },
            "behavior": {
                "urgency": "high",
                "pressure_language": True,
                "skipped_verification_steps": False,
                "unusual_session_behavior": True,
                "sources": {
                    "urgency": "simulated",
                    "pressure_language": "simulated",
                    "skipped_verification_steps": "simulated",
                    "unusual_session_behavior": "simulated"
                }
            },
            "transaction": {
                "action_type": "fund_transfer",
                "amount_inr": 200000,
                "usual_amount_inr": 20000,
                "recipient_label": "New beneficiary account",
                "new_recipient": True,
                "recipient_account_age_days": 7,
                "tx_last_hour": 0,
                "sources": {
                    "action_type": "simulated",
                    "amount_inr": "simulated",
                    "usual_amount_inr": "simulated",
                    "recipient_label": "simulated",
                    "new_recipient": "simulated",
                    "recipient_account_age_days": "simulated",
                    "tx_last_hour": "simulated"
                }
            },
            "evidence_ids": []
        }
    },
    {
        "id": "forged-credential",
        "title": "Forged credential: identity mismatch",
        "narrative": "Face and voice do not match the claimed identity and the credential document shows tampering, while everything else looks routine.",
        "expected_decision": "BLOCK",
        "featured": False,
        "payload": {
            "identity": {
                "claimed_name": "User",
                "claimed_role": "User",
                "credential_verified": False,
                "face_match": 22,
                "voice_match": 30,
                "liveness_ok": True,
                "document_tampered": True,
                "sources": {
                    "face_match": "simulated",
                    "voice_match": "simulated",
                    "liveness_ok": "simulated",
                    "document_tampered": "simulated"
                }
            },
            "context": {
                "known_device": True,
                "location_matches_pattern": True,
                "remote_access_tool": False,
                "local_hour": 11,
                "sources": {
                    "known_device": "simulated",
                    "location_matches_pattern": "simulated",
                    "remote_access_tool": "simulated",
                    "local_hour": "simulated"
                }
            },
            "behavior": {
                "urgency": "low",
                "pressure_language": False,
                "skipped_verification_steps": False,
                "unusual_session_behavior": False,
                "sources": {
                    "urgency": "simulated",
                    "pressure_language": "simulated",
                    "skipped_verification_steps": "simulated",
                    "unusual_session_behavior": "simulated"
                }
            },
            "transaction": {
                "action_type": "fund_transfer",
                "amount_inr": 30000,
                "usual_amount_inr": 30000,
                "recipient_label": "Existing",
                "new_recipient": False,
                "recipient_account_age_days": 900,
                "tx_last_hour": 0,
                "sources": {
                    "action_type": "simulated",
                    "amount_inr": "simulated",
                    "usual_amount_inr": "simulated",
                    "recipient_label": "simulated",
                    "new_recipient": "simulated",
                    "recipient_account_age_days": "simulated",
                    "tx_last_hour": "simulated"
                }
            },
            "evidence_ids": []
        }
    }
]
