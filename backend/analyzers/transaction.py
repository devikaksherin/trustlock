import time
from ..config import HIGH_VALUE_INR
from ..schemas import TransactionInput, AnalyzerResult, Reason, Signal, Profile, AnalyzeRequest
from typing import Optional

# TODO(real-model): anomaly model, amount-baseline model

def analyze_transaction(inp: TransactionInput, profile: Optional[Profile] = None, request: Optional[AnalyzeRequest] = None) -> AnalyzerResult:
    start_time = time.perf_counter()
    penalties = 0
    reasons = []
    signals = []
    
    def get_source(field: str) -> str:
        return inp.sources.get(field, "user_supplied")

    if profile and request:
        from .profile import compare_to_profile
        comp = compare_to_profile(profile, request)
        if comp.new_recipient is not None:
            inp.new_recipient = comp.new_recipient
            inp.sources["new_recipient"] = "profile"
        if comp.usual_amount_inr is not None:
            inp.usual_amount_inr = comp.usual_amount_inr
            inp.sources["usual_amount_inr"] = "profile"
        if comp.amount_ratio is not None:
            inp.sources["amount_inr"] = "profile"

    
    def add_reason(severity: str, title: str, description: str, source: str):
        reasons.append(Reason(
            category="transaction",
            severity=severity,
            title=title,
            description=description,
            source=source
        ))
        
    def add_signal(key: str, label: str, value: any, source: str):
        signals.append(Signal(
            key=key,
            label=label,
            value=value,
            source=source
        ))

    add_signal("action_type", "Action Type", inp.action_type, get_source("action_type"))
    add_signal("amount_inr", "Amount (INR)", inp.amount_inr, get_source("amount_inr"))
    add_signal("new_recipient", "New Recipient", inp.new_recipient, get_source("new_recipient"))
    add_signal("tx_last_hour", "Tx Last Hour", inp.tx_last_hour, get_source("tx_last_hour"))
    
    if inp.amount_inr is not None and inp.usual_amount_inr is not None and inp.usual_amount_inr > 0:
        ratio = inp.amount_inr / inp.usual_amount_inr
        if ratio >= 10:
            penalties += 40
            add_reason("high", "Amount unusually high", f"Amount is {ratio:.1f}x the usual baseline.", get_source("amount_inr"))
        elif ratio >= 3:
            penalties += 20
            add_reason("medium", "Amount higher than usual", f"Amount is {ratio:.1f}x the usual baseline.", get_source("amount_inr"))
            
    if inp.amount_inr is not None and inp.amount_inr >= HIGH_VALUE_INR:
        penalties += 20
        add_reason("medium", "High value transaction", f"Transaction amount exceeds high value threshold.", get_source("amount_inr"))
        
    if inp.new_recipient:
        penalties += 30
        add_reason("high", "New recipient", "Transfer to a newly seen or unknown recipient.", get_source("new_recipient"))
    else:
        add_reason("pass", "Existing recipient", "Recipient is known.", get_source("new_recipient"))
        
    if inp.recipient_account_age_days is not None and inp.recipient_account_age_days < 30:
        penalties += 15
        add_reason("medium", "New account", "Recipient account is newly established.", get_source("recipient_account_age_days"))
        
    if inp.tx_last_hour >= 3:
        penalties += 20
        add_reason("medium", "High velocity", "Multiple transactions in the last hour.", get_source("tx_last_hour"))
        
    sub_risk = min(100, penalties)
    sub_trust = 100 - sub_risk
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    return AnalyzerResult(
        category="transaction",
        sub_risk=sub_risk,
        sub_trust=sub_trust,
        signals=signals,
        reasons=reasons,
        duration_ms=duration_ms
    )
