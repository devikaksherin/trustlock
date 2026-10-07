import pytest
from backend.risk_engine import analyze, decide
from backend.schemas import (
    AnalyzeRequest, IdentityInput, ContextInput, BehaviorInput, TransactionInput
)
from backend.config import WEIGHTS

@pytest.fixture
def scenario_1():
    return AnalyzeRequest(
        identity=IdentityInput(
            claimed_name="Officer R. Menon", claimed_role="District Fire Officer",
            credential_verified=True, face_match=92, voice_match=90, liveness_ok=True
        ),
        context=ContextInput(
            known_device=True, location_matches_pattern=True, remote_access_tool=False, local_hour=11
        ),
        behavior=BehaviorInput(
            urgency="low", pressure_language=False, skipped_verification_steps=False, unusual_session_behavior=False
        ),
        transaction=TransactionInput(
            action_type="fund_transfer", amount_inr=4500, usual_amount_inr=5000,
            recipient_label="Existing vendor account", new_recipient=False, recipient_account_age_days=900, tx_last_hour=0
        )
    )

@pytest.fixture
def scenario_2():
    return AnalyzeRequest(
        identity=IdentityInput(
            claimed_name="Unknown", claimed_role="User",
            credential_verified=False, face_match=85, voice_match=84, liveness_ok=True
        ),
        context=ContextInput(
            known_device=False, location_matches_pattern=False, remote_access_tool=True, local_hour=14
        ),
        behavior=BehaviorInput(
            urgency="medium", pressure_language=False, skipped_verification_steps=False, unusual_session_behavior=False
        ),
        transaction=TransactionInput(
            action_type="fund_transfer", amount_inr=25000, usual_amount_inr=20000,
            recipient_label="New Payee", new_recipient=True, recipient_account_age_days=None, tx_last_hour=0
        )
    )

@pytest.fixture
def scenario_3():
    return AnalyzeRequest(
        identity=IdentityInput(
            claimed_name="Officer", claimed_role="Officer",
            credential_verified=False, face_match=88, voice_match=86, liveness_ok=True
        ),
        context=ContextInput(
            known_device=False, location_matches_pattern=False, remote_access_tool=False, local_hour=2
        ),
        behavior=BehaviorInput(
            urgency="high", pressure_language=True, skipped_verification_steps=False, unusual_session_behavior=True
        ),
        transaction=TransactionInput(
            action_type="fund_transfer", amount_inr=200000, usual_amount_inr=20000,
            recipient_label="New beneficiary account", new_recipient=True, recipient_account_age_days=7, tx_last_hour=0
        )
    )

@pytest.fixture
def scenario_4():
    return AnalyzeRequest(
        identity=IdentityInput(
            claimed_name="User", claimed_role="User",
            credential_verified=False, face_match=22, voice_match=30, liveness_ok=True, document_tampered=True
        ),
        context=ContextInput(
            known_device=True, location_matches_pattern=True, remote_access_tool=False, local_hour=11
        ),
        behavior=BehaviorInput(
            urgency="low", pressure_language=False, skipped_verification_steps=False, unusual_session_behavior=False
        ),
        transaction=TransactionInput(
            action_type="fund_transfer", amount_inr=30000, usual_amount_inr=30000,
            recipient_label="Existing", new_recipient=False, recipient_account_age_days=900, tx_last_hour=0
        )
    )

def test_weights_sum():
    assert sum(WEIGHTS.values()) == 1.0

def test_boundaries():
    assert decide(70)[0] == "ALLOW"
    assert decide(69)[0] == "VERIFY"
    assert decide(40)[0] == "VERIFY"
    assert decide(39)[0] == "BLOCK"

def test_determinism(scenario_3):
    first = analyze(scenario_3).model_dump_json()
    for _ in range(100):
        # Need to patch time inside analyze to avoid duration_ms making json diff, but for now we ignore duration_ms or timestamp for exact string match
        # Let's compare the objects ignoring timestamp and trace
        res = analyze(scenario_3)
        res_dict = res.model_dump()
        del res_dict['timestamp']
        for t in res_dict['trace']:
            del t['duration_ms']
            
        first_dict = analyze(scenario_3).model_dump()
        del first_dict['timestamp']
        for t in first_dict['trace']:
            del t['duration_ms']
        
        assert res_dict == first_dict

def test_scenarios_and_print(scenario_1, scenario_2, scenario_3, scenario_4):
    print("\n--- SCENARIO EVALUATION ---")
    
    # Scenario 1
    res1 = analyze(scenario_1)
    assert res1.decision == "ALLOW"
    assert res1.trust_score >= 85
    print_scenario(1, res1)
    
    # Scenario 2
    res2 = analyze(scenario_2)
    assert res2.decision == "VERIFY"
    assert 40 <= res2.trust_score <= 69
    print_scenario(2, res2)
    
    # Scenario 3
    res3 = analyze(scenario_3)
    assert res3.decision == "BLOCK"
    assert res3.trust_score <= 39
    assert any(r.category == "convergence" for r in res3.reasons)
    assert res3.scores["identity"] == 82
    print_scenario(3, res3)
    
    # Scenario 4
    res4 = analyze(scenario_4)
    assert res4.decision == "BLOCK"
    assert any(p.id == "P1" for p in res4.policy)
    assert "Blocked by policy rule" in res4.summary
    print_scenario(4, res4)
    
def print_scenario(num, res):
    print(f"\nScenario {num}:")
    print(f"Trust Score: {res.trust_score}, Decision: {res.decision}")
    print("Top 3 Reasons:")
    for i, reason in enumerate(res.reasons[:3]):
        print(f"  {i+1}. [{reason.severity.upper()}] {reason.title} - {reason.description}")
