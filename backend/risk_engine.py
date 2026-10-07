import math
from datetime import datetime, timezone
from .config import WEIGHTS, THRESHOLDS, CONVERGENCE_MIN_CATEGORIES, CONVERGENCE_SUBRISK, CONVERGENCE_BONUS, CONFIG_VERSION
from .schemas import (
    AnalyzeRequest, AnalyzeResponse, Breakdown, Reason, Policy, Trace
)
from .analyzers.identity import analyze_identity
from .analyzers.context import analyze_context
from .analyzers.behavior import analyze_behavior
from .analyzers.transaction import analyze_transaction

def compute_risk(results) -> tuple[float, list[Breakdown]]:
    total_risk = 0.0
    breakdown = []
    
    for res in results:
        weight = WEIGHTS.get(res.category, 0.0)
        contribution = weight * res.sub_risk
        total_risk += contribution
        breakdown.append(Breakdown(
            category=res.category,
            weight=weight,
            sub_trust=res.sub_trust,
            sub_risk=res.sub_risk,
            contribution=contribution
        ))
    
    return total_risk, breakdown

def apply_convergence(risk: float, results: list) -> tuple[float, float, Reason | None]:
    high_risk_cats = [r for r in results if r.sub_risk >= CONVERGENCE_SUBRISK]
    if len(high_risk_cats) >= CONVERGENCE_MIN_CATEGORIES:
        risk += CONVERGENCE_BONUS
        reason = Reason(
            category="convergence",
            severity="high",
            title="Multiple independent signals converge",
            description="Several independent risk factors are present simultaneously.",
            source="measured"
        )
        return min(100.0, risk), CONVERGENCE_BONUS, reason
    return risk, 0.0, None

def apply_policy(request: AnalyzeRequest) -> tuple[str | None, list[Policy]]:
    floor = None
    policies = []
    
    # P1: identity inconsistent or document tampered -> floor BLOCK
    if request.identity.face_match < 50 or request.identity.voice_match < 50 or request.identity.document_tampered:
        floor = "BLOCK"
        policies.append(Policy(
            id="P1",
            title="Identity inconsistent",
            effect="Decision cannot be better than BLOCK"
        ))
        
    return floor, policies

def decide(trust_score: int, floor: str | None = None) -> tuple[str, str]:
    if trust_score >= THRESHOLDS["allow_min"]:
        base_decision = "ALLOW"
    elif trust_score >= THRESHOLDS["verify_min"]:
        base_decision = "VERIFY"
    else:
        base_decision = "BLOCK"
        
    if floor == "BLOCK":
        decision = "BLOCK"
    elif floor == "VERIFY" and base_decision == "ALLOW":
        decision = "VERIFY"
    else:
        decision = base_decision
        
    if decision == "ALLOW":
        risk_level = "LOW"
    elif decision == "VERIFY":
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
        
    return decision, risk_level

def severity_rank(severity: str) -> int:
    ranks = {"high": 1, "medium": 2, "low": 3, "pass": 4}
    return ranks.get(severity, 5)

def analyze(request: AnalyzeRequest, evidence: list = [], case_id: str = "TL-PREVIEW", profile_data: dict = None) -> AnalyzeResponse:
    # Build Profile object if passed
    profile_obj = None
    if profile_data:
        from .schemas import Profile
        profile_obj = Profile(**profile_data)

    # Run analyzers
    results = [
        analyze_identity(request.identity, evidence),
        analyze_context(request.context, profile_obj, request),
        analyze_behavior(request.behavior),
        analyze_transaction(request.transaction, profile_obj, request)
    ]
    
    # Trace
    trace = [Trace(stage=r.category, duration_ms=r.duration_ms) for r in results]
    
    # Compute Risk
    risk, breakdown = compute_risk(results)
    
    # Convergence
    risk, convergence_bonus, convergence_reason = apply_convergence(risk, results)
    
    # Calculate Trust
    trust_score = math.floor((100 - risk) + 0.5)
    risk_score = 100 - trust_score
    
    # Policy
    floor, policies = apply_policy(request)
    
    # Decide
    decision, risk_level = decide(trust_score, floor)
    
    # Aggregate reasons and signals
    reasons = []
    signals = []
    scores = {}
    for r in results:
        reasons.extend(r.reasons)
        signals.extend(r.signals)
        scores[r.category] = r.sub_trust
        
    if convergence_reason:
        reasons.append(convergence_reason)
        
    # Sort reasons
    reasons.sort(key=lambda x: severity_rank(x.severity))
    
    # Generate summary
    if floor == "BLOCK" and decision == "BLOCK":
        summary = "Blocked by policy rule: Identity inconsistent or document tampered."
    else:
        flagged = [b.category for b in breakdown if b.sub_risk >= 30]
        if decision == "ALLOW":
            summary = "Action appears low risk."
        elif decision == "VERIFY":
            summary = f"Verification required: moderate risk in {', '.join(flagged)}."
        else:
            summary = f"Blocked: high risk indicators found in {', '.join(flagged)}."
            
        if convergence_reason:
            summary += " Multiple signals converge."
            
    # Build evidence summary
    evidence_summary = []
    for ev in evidence:
        evidence_summary.append({
            "id": ev["id"],
            "kind": ev["kind"],
            "original_name": ev["original_name"],
            "sha256": ev["sha256"],
            "findings": ev.get("findings", [])
        })
            
    return AnalyzeResponse(
        case_id=case_id,
        trust_score=trust_score,
        risk_score=risk_score,
        decision=decision,
        risk_level=risk_level,
        summary=summary,
        scores=scores,
        breakdown=breakdown,
        reasons=reasons,
        policy=policies,
        signals=signals,
        convergence_bonus=convergence_bonus,
        evidence=evidence_summary,
        trace=trace,
        challenge_id=None,
        config_version=CONFIG_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
