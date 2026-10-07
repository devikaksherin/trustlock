import time
from ..config import MEDIA_RISK_CAP
from ..schemas import IdentityInput, AnalyzerResult, Reason, Signal

# TODO(real-model): MediaPipe/OpenCV liveness, speaker verification
# Note: Face/voice/liveness are simulated or user-supplied inputs, never real detection.

def analyze_identity(inp: IdentityInput, evidence_findings=[]) -> AnalyzerResult:
    start_time = time.perf_counter()
    penalties = 0
    reasons = []
    signals = []
    
    def get_source(field: str) -> str:
        return inp.sources.get(field, "user_supplied")
    
    def add_reason(severity: str, title: str, description: str, source: str):
        reasons.append(Reason(
            category="identity",
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

    add_signal("face_match", "Face Match", inp.face_match, get_source("face_match"))
    add_signal("voice_match", "Voice Match", inp.voice_match, get_source("voice_match"))
    add_signal("liveness_ok", "Liveness", inp.liveness_ok, get_source("liveness_ok"))
    
    if inp.face_match < 50 or inp.voice_match < 50:
        penalties += 50
        add_reason("high", "Identity inconsistent", "Face or voice match is below acceptable threshold.", get_source("face_match" if inp.face_match < 50 else "voice_match"))
    else:
        add_reason("pass", "Face and voice signals consistent", "Identity biometrics appear to match.", get_source("face_match"))
        
    if inp.document_tampered:
        penalties += 40
        add_reason("high", "Document tampered", "ID document shows signs of tampering.", get_source("document_tampered"))
        
    if not inp.credential_verified:
        penalties += 18
        add_reason("medium", "Credential unverified", "The claimed role or credential could not be verified.", get_source("credential_verified"))
    else:
        add_reason("pass", "Credential verified", "The claimed role or credential has been verified.", get_source("credential_verified"))
        
    if not inp.liveness_ok:
        penalties += 25
        add_reason("medium", "Weak liveness", "Liveness check failed.", get_source("liveness_ok"))
        
    # Process measured media/document hints (capped)
    measured_risk = 0
    for finding in evidence_findings:
        hint = finding.get("risk_hint", 0)
        measured_risk += hint
        if hint > 0:
            filename = finding.get("original_name", "Unknown File")
            add_reason(
                severity="medium" if hint >= 10 else "low",
                title="Media/document indicators",
                description=f"{filename}: measured risk indicators found (+{hint}). This is an indicator, not proof of forgery.",
                source="measured"
            )
        
    if measured_risk > 0:
        capped_measured = min(measured_risk, MEDIA_RISK_CAP)
        penalties += capped_measured

    sub_risk = min(100, penalties)
    sub_trust = 100 - sub_risk
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    return AnalyzerResult(
        category="identity",
        sub_risk=sub_risk,
        sub_trust=sub_trust,
        signals=signals,
        reasons=reasons,
        duration_ms=duration_ms
    )
