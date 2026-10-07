import time
from ..schemas import ContextInput, AnalyzerResult, Reason, Signal, Profile, AnalyzeRequest
from typing import Optional

# TODO(real-model): device fingerprinting

def analyze_context(inp: ContextInput, profile: Optional[Profile] = None, request: Optional[AnalyzeRequest] = None) -> AnalyzerResult:
    start_time = time.perf_counter()
    penalties = 0
    reasons = []
    signals = []
    
    def get_source(field: str) -> str:
        return inp.sources.get(field, "user_supplied")

    if profile and request:
        from .profile import compare_to_profile
        comp = compare_to_profile(profile, request)
        if comp.known_device is not None:
            inp.known_device = comp.known_device
            inp.sources["known_device"] = "profile"
        if comp.location_matches is not None:
            inp.location_matches_pattern = comp.location_matches
            inp.sources["location_matches_pattern"] = "profile"
        if comp.hour_typical is not None:
            inp.sources["local_hour"] = "profile"

    
    def add_reason(severity: str, title: str, description: str, source: str):
        reasons.append(Reason(
            category="context",
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

    add_signal("known_device", "Known Device", inp.known_device, get_source("known_device"))
    add_signal("location_matches_pattern", "Location", inp.location_matches_pattern, get_source("location_matches_pattern"))
    add_signal("remote_access_tool", "Remote Access Tool", inp.remote_access_tool, get_source("remote_access_tool"))
    add_signal("local_hour", "Local Hour", inp.local_hour, get_source("local_hour"))
    
    if not inp.known_device:
        penalties += 30
        add_reason("high", "New device detected", "The request came from a device not linked to this account.", get_source("known_device"))
    else:
        add_reason("pass", "Known device", "Device is recognized.", get_source("known_device"))
        
    if not inp.location_matches_pattern:
        penalties += 30
        add_reason("high", "Unusual location", "The request originates from an unexpected location.", get_source("location_matches_pattern"))
    else:
        add_reason("pass", "Location matches usual pattern", "Location is consistent with user history.", get_source("location_matches_pattern"))
        
    if inp.remote_access_tool:
        penalties += 25
        add_reason("medium", "Remote access tool detected", "A remote desktop or screen sharing tool is active.", get_source("remote_access_tool"))
        
    if 0 <= inp.local_hour <= 5:
        penalties += 12
        add_reason("low", "Unusual hour", "Action performed during unusual local hours (00:00 - 05:00).", get_source("local_hour"))
        
    sub_risk = min(100, penalties)
    sub_trust = 100 - sub_risk
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    return AnalyzerResult(
        category="context",
        sub_risk=sub_risk,
        sub_trust=sub_trust,
        signals=signals,
        reasons=reasons,
        duration_ms=duration_ms
    )
