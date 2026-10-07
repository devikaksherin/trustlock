import time
from ..schemas import BehaviorInput, AnalyzerResult, Reason, Signal

def analyze_behavior(inp: BehaviorInput) -> AnalyzerResult:
    start_time = time.perf_counter()
    penalties = 0
    reasons = []
    signals = []
    
    def get_source(field: str) -> str:
        return inp.sources.get(field, "user_supplied")
    
    def add_reason(severity: str, title: str, description: str, source: str):
        reasons.append(Reason(
            category="behavior",
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

    add_signal("urgency", "Urgency", inp.urgency, get_source("urgency"))
    add_signal("pressure_language", "Pressure Language", inp.pressure_language, get_source("pressure_language"))
    add_signal("skipped_verification_steps", "Skipped Verification", inp.skipped_verification_steps, get_source("skipped_verification_steps"))
    add_signal("unusual_session_behavior", "Unusual Session", inp.unusual_session_behavior, get_source("unusual_session_behavior"))
    
    urgency_penalty = 0
    if inp.urgency == "critical":
        urgency_penalty = 40
    elif inp.urgency == "high":
        urgency_penalty = 30
    elif inp.urgency == "medium":
        urgency_penalty = 10
        
    if urgency_penalty > 0:
        penalties += urgency_penalty
        sev = "high" if urgency_penalty >= 30 else ("medium" if urgency_penalty >= 15 else "low")
        add_reason(sev, f"Urgency: {inp.urgency}", "High urgency indicated.", get_source("urgency"))
        
    if inp.pressure_language:
        penalties += 20
        add_reason("medium", "Pressure language", "Use of coercive or high-pressure phrasing.", get_source("pressure_language"))
        
    if inp.skipped_verification_steps:
        penalties += 20
        add_reason("medium", "Skipped verification steps", "Normal verification processes were bypassed.", get_source("skipped_verification_steps"))
        
    if inp.unusual_session_behavior:
        penalties += 20
        add_reason("medium", "Unusual session behavior", "Interaction patterns deviate from the norm.", get_source("unusual_session_behavior"))
        
    sub_risk = min(100, penalties)
    sub_trust = 100 - sub_risk
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    return AnalyzerResult(
        category="behavior",
        sub_risk=sub_risk,
        sub_trust=sub_trust,
        signals=signals,
        reasons=reasons,
        duration_ms=duration_ms
    )
