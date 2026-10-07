from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List

class Signal(BaseModel):
    key: str
    label: str
    value: Any
    source: str
    confidence: Optional[float] = None
    detail: Optional[str] = None

class IdentityInput(BaseModel):
    claimed_name: str
    claimed_role: str
    credential_verified: bool
    face_match: int = Field(ge=0, le=100)
    voice_match: int = Field(ge=0, le=100)
    liveness_ok: bool
    document_tampered: bool = False
    sources: Dict[str, str] = Field(default_factory=dict)

class ContextInput(BaseModel):
    known_device: bool
    location_matches_pattern: bool
    remote_access_tool: bool
    local_hour: int = Field(ge=0, le=23)
    device_label: Optional[str] = None
    location_label: Optional[str] = None
    sources: Dict[str, str] = Field(default_factory=dict)

class BehaviorInput(BaseModel):
    urgency: Literal["low", "medium", "high", "critical"]
    pressure_language: bool
    skipped_verification_steps: bool
    unusual_session_behavior: bool
    sources: Dict[str, str] = Field(default_factory=dict)

class TransactionInput(BaseModel):
    action_type: Literal["fund_transfer", "resource_redirection", "access_change"]
    amount_inr: Optional[float] = None
    usual_amount_inr: Optional[float] = None
    recipient_label: str
    new_recipient: bool
    recipient_account_age_days: Optional[int] = None
    tx_last_hour: int = 0
    sources: Dict[str, str] = Field(default_factory=dict)

class AnalyzeRequest(BaseModel):
    identity: IdentityInput
    context: ContextInput
    behavior: BehaviorInput
    transaction: TransactionInput
    evidence_ids: List[str] = Field(default_factory=list)
    scenario_id: Optional[str] = None
    profile_id: Optional[str] = None

class Reason(BaseModel):
    category: str
    severity: Literal["high", "medium", "low", "pass"]
    title: str
    description: str
    source: str

class Breakdown(BaseModel):
    category: str
    weight: float
    sub_trust: int
    sub_risk: int
    contribution: float

class AnalyzerResult(BaseModel):
    category: str
    sub_risk: int
    sub_trust: int
    signals: List[Signal]
    reasons: List[Reason]
    duration_ms: float

class Policy(BaseModel):
    id: str
    title: str
    effect: str

class Trace(BaseModel):
    stage: str
    duration_ms: float

class EvidenceRecord(BaseModel):
    id: str
    original_name: str
    kind: str
    mime: str
    size_bytes: int
    sha256: str
    uploaded_at: str

class ChallengeGenerateRequest(BaseModel):
    case_id: str
    decision: str

class ChallengeGenerateResponse(BaseModel):
    challenge_id: str
    case_id: str
    type: str
    instruction: str
    status: str
    expires_at: str
    ttl_seconds: int
    attempts_left: int
    prototype: bool

class ChallengeVerifyRequest(BaseModel):
    challenge_id: str
    response: Optional[str] = None
    simulation: bool = False
    simulated_outcome: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)

class ChallengeViewResponse(BaseModel):
    challenge_id: str
    case_id: str
    type: str
    instruction: str
    status: str
    attempts_left: int
    ttl_seconds: int
    remaining_seconds: int
    expired: bool
    expires_at: str
    final_decision: Optional[str] = None
    human_review: bool = False
    final_note: Optional[str] = None
    prototype: bool = True

class ChallengeVerifyResponse(BaseModel):
    challenge_id: str
    status: str
    similarity: Optional[float] = None
    attempts_left: int
    reason: str
    final_decision: Optional[str] = None
    human_review: bool = False
    final_note: str
    checks: str
    face_count: Optional[int] = None
    multiple_faces_detected: Optional[bool] = None
    visual_presence_passed: Optional[bool] = None
    audio_passed: Optional[bool] = None
    challenge_passed: Optional[bool] = None
    prototype: bool

class HistoryRecord(BaseModel):
    pass

class AnalyzeResponse(BaseModel):
    case_id: str
    trust_score: int
    risk_score: int
    decision: str
    risk_level: str
    summary: str
    scores: Dict[str, int]
    breakdown: List[Breakdown]
    reasons: List[Reason]
    policy: List[Policy]
    signals: List[Signal]
    convergence_bonus: float
    evidence: List[dict]
    trace: List[Trace]
    challenge_id: Optional[str] = None
    config_version: str
    timestamp: str

class TransactionPattern(BaseModel):
    id: str
    category: str
    min_amount: float
    max_amount: float
    typical_payees: List[str] = Field(default_factory=list)
    frequency: str
    usual_days: str
    notes: Optional[str] = None

class NormalHours(BaseModel):
    start: int
    end: int

class Baseline(BaseModel):
    usual_devices: List[str] = Field(default_factory=list)
    usual_locations: List[str] = Field(default_factory=list)
    normal_hours: NormalHours
    usual_channels: List[str] = Field(default_factory=list)
    trusted_contacts: List[str] = Field(default_factory=list)
    trusted_issuers: List[str] = Field(default_factory=list)
    transaction_patterns: List[TransactionPattern] = Field(default_factory=list)

class Profile(BaseModel):
    id: str
    display_name: str
    user_id: str
    role: str
    organisation: str
    baseline: Baseline
    notes: str = ""
    created_at: str
    updated_at: str
    demo: bool = False
