import secrets
import difflib
import uuid
import re
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from .config import (
    CHALLENGE_TTL_SECONDS,
    CHALLENGE_MAX_ATTEMPTS,
    CHALLENGE_VERIFY_SIMILARITY,
    CHALLENGE_RETRY_SIMILARITY,
    NONCE_WORDS
)
from .storage import storage

class NotFound(Exception): pass
class Closed(Exception): pass
class ValidationError(Exception): pass

TEMPLATES = [
    {"type": "voice_phrase", "text": "Look at the camera and say {NONCE} clearly."},
    {"type": "voice_phrase", "text": "Say {NONCE} slowly, then say it once more."},
    {"type": "head_pose", "text": "Turn your head to the right and say {NONCE}."},
    {"type": "head_pose", "text": "Look up briefly, then face the camera and say {NONCE}."},
    {"type": "object_presence", "text": "Hold a blue object next to your face and say {NONCE}."},
    {"type": "object_presence", "text": "Hold up three fingers beside your face and say {NONCE}."}
]

def now():
    return datetime.now(timezone.utc)

def generate_challenge(case_id: str, decision: str):
    if decision not in ("VERIFY", "BLOCK"):
        raise ValueError("no challenge needed")
        
    template = secrets.choice(TEMPLATES)
    word = secrets.choice(NONCE_WORDS)
    num = secrets.choice(range(10, 100))
    nonce = f"{word}-{num}"
    
    instruction = template["text"].replace("{NONCE}", nonce)
    
    challenge_id = str(uuid.uuid4())
    created_at = now()
    expires_at = created_at + timedelta(seconds=CHALLENGE_TTL_SECONDS)
    
    record = {
        "id": challenge_id,
        "case_id": case_id,
        "original_decision": decision,
        "type": template["type"],
        "instruction": instruction,
        "nonce": nonce,
        "status": "pending",
        "attempts_left": CHALLENGE_MAX_ATTEMPTS,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat()
    }
    
    storage.save_challenge(record)
    
    return {
        "challenge_id": challenge_id,
        "case_id": case_id,
        "type": template["type"],
        "instruction": instruction,
        "status": "pending",
        "expires_at": record["expires_at"],
        "ttl_seconds": CHALLENGE_TTL_SECONDS,
        "attempts_left": CHALLENGE_MAX_ATTEMPTS,
        "prototype": True
    }

_NUM_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19
}
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
}

def normalize_phrase(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]', ' ', text)
    tokens = text.split()
    
    out = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in _TENS:
            if i + 1 < len(tokens) and tokens[i+1] in _NUM_WORDS and _NUM_WORDS[tokens[i+1]] < 10:
                out.append(str(_TENS[t] + _NUM_WORDS[tokens[i+1]]))
                i += 2
            else:
                out.append(str(_TENS[t]))
                i += 1
        elif t in _NUM_WORDS:
            out.append(str(_NUM_WORDS[t]))
            i += 1
        else:
            out.append(t)
            i += 1
            
    return " ".join(out)

def phrase_similarity(expected: str, heard: str) -> float:
    return difflib.SequenceMatcher(None, expected, heard).ratio()

def phrase_matches(expected: str, heard: str) -> tuple[str, float]:
    expected_norm = normalize_phrase(expected)
    heard_norm = normalize_phrase(heard)
    
    expected_tokens = expected_norm.split()
    heard_tokens = heard_norm.split()
    
    similarity = phrase_similarity(expected_norm, heard_norm)
    
    # Check if expected is contiguous inside heard
    verified = False
    if len(expected_tokens) > 0 and len(expected_tokens) <= len(heard_tokens):
        for i in range(len(heard_tokens) - len(expected_tokens) + 1):
            if heard_tokens[i:i+len(expected_tokens)] == expected_tokens:
                verified = True
                break
                
    if not verified:
        if similarity >= CHALLENGE_VERIFY_SIMILARITY:
            # Check every digit token
            expected_digits = [t for t in expected_tokens if t.isdigit()]
            heard_digits = [t for t in heard_tokens if t.isdigit()]
            if all(d in heard_digits for d in expected_digits) and len(expected_digits) > 0:
                verified = True
                
    if verified:
        return "verified", similarity
    elif similarity >= CHALLENGE_RETRY_SIMILARITY:
        return "retry", similarity
    else:
        return "failed", similarity

def verify_challenge(challenge_id: str, response: str = None, simulation: bool = False, simulated_outcome: str = None, evidence_ids: list[str] = None):
    ch = storage.get_challenge(challenge_id)
    if not ch:
        raise NotFound("challenge not found")
        
    if ch["status"] in ("verified", "failed"):
        raise Closed("challenge closed")
        
    attempts = ch["attempts_left"] - 1
    
    expires_at = datetime.fromisoformat(ch["expires_at"])
    
    if now() > expires_at:
        outcome = "failed"
        reason = "expired"
        similarity = None
        checks = "expired"
    elif simulation:
        if simulated_outcome not in ("pass", "fail", "unclear"):
            raise ValidationError("invalid simulated_outcome")
        if simulated_outcome == "pass":
            outcome = "verified"
            reason = "simulated"
        elif simulated_outcome == "fail":
            outcome = "failed"
            reason = "simulated"
        else:
            outcome = "retry"
            reason = "simulated"
        similarity = None
        checks = "simulation"
    else:
        # AUDIO VERIFICATION
        audio_passed = False
        if not response:
            audio_outcome = "retry"
            audio_reason = "phrase_not_checked"
            similarity = 0.0
            audio_checks = "phrase_not_checked"
        else:
            audio_outcome, similarity = phrase_matches(ch["nonce"], response)
            audio_reason = "match" if audio_outcome == "verified" else "mismatch"
            audio_checks = "phrase_match_only"
            if audio_outcome == "verified":
                audio_passed = True
                
        # VISUAL VERIFICATION
        face_count = None
        multiple_faces_detected = False
        visual_presence_passed = False

        if evidence_ids:
            for eid in evidence_ids:
                ev = storage.get_evidence(eid)
                if ev and ev.get("findings"):
                    for f in ev["findings"]:
                        if f["key"] == "face_count":
                            val = int(f["value"])
                            if face_count is None or val > face_count:
                                face_count = val

        if face_count == 1:
            visual_presence_passed = True
        elif face_count is not None and face_count > 1:
            multiple_faces_detected = True

        # FINAL VERIFICATION DECISION
        challenge_passed = False
        
        if audio_passed and visual_presence_passed:
            outcome = "verified"
            reason = "Visual and audio verification passed"
            checks = "full_verification"
            challenge_passed = True
        elif audio_passed and not visual_presence_passed:
            outcome = "failed"
            if multiple_faces_detected:
                reason = "Multiple people were detected. Only one person may be present."
            else:
                reason = "No person was detected in the verification video."
            checks = "visual_failed"
        elif not audio_passed and visual_presence_passed:
            outcome = audio_outcome
            reason = audio_reason
            checks = audio_checks
        else:
            # Both failed
            outcome = audio_outcome # usually retry or failed
            if multiple_faces_detected:
                reason = "Multiple people were detected and audio mismatch."
            elif face_count == 0 or face_count is None:
                reason = "No person was detected and audio mismatch."
            else:
                reason = audio_reason
            checks = "both_failed"
            
    if outcome == "retry" and attempts <= 0:
        outcome = "failed"
        reason = "attempts_exhausted"
        
    updates = {
        "attempts_left": attempts,
        "last_outcome": outcome
    }
    
    final_decision = None
    human_review = False
    final_note = ""
    status = ch["status"]
    
    if outcome in ("verified", "failed"):
        updates["status"] = outcome
        updates["resolved_at"] = now().isoformat()
        
        orig = ch["original_decision"]
        if orig == "VERIFY":
            if outcome == "verified":
                final_decision = "ALLOW"
                final_note = "Challenge passed. Step-up verification satisfied; the action may proceed."
            else:
                final_decision = "BLOCK"
                final_note = "Challenge failed. The action is blocked."
        elif orig == "BLOCK":
            if outcome == "verified":
                final_decision = "BLOCK"
                human_review = True
                final_note = "Challenge passed, but a passed challenge alone cannot release a high-risk action. Routed to human review."
            else:
                final_decision = "BLOCK"
                final_note = "Challenge failed. Block confirmed."
                
        updates["final_decision"] = final_decision
        updates["final_note"] = final_note
    else:
        final_note = f"Attempts left: {attempts}"
        
    db_updates = {k: v for k, v in updates.items() if k != "human_review"}
    storage.update_challenge(challenge_id, db_updates)
    
    if outcome in ("verified", "failed"):
        storage.append_event("CHALLENGE_RESULT", ch["case_id"], {
            "challenge_id": challenge_id,
            "outcome": outcome,
            "reason": reason,
            "attempts_left": attempts,
            "final_decision": final_decision,
            "human_review": human_review,
            "final_note": final_note,
            "checks": checks,
            "evidence_ids": evidence_ids or []
        })
    
    return {
        "challenge_id": challenge_id,
        "status": outcome,
        "similarity": similarity,
        "attempts_left": attempts,
        "reason": reason,
        "final_decision": final_decision,
        "human_review": human_review,
        "final_note": final_note,
        "checks": checks,
        "face_count": face_count if 'face_count' in locals() else None,
        "multiple_faces_detected": multiple_faces_detected if 'multiple_faces_detected' in locals() else None,
        "visual_presence_passed": visual_presence_passed if 'visual_presence_passed' in locals() else None,
        "audio_passed": audio_passed if 'audio_passed' in locals() else None,
        "challenge_passed": challenge_passed if 'challenge_passed' in locals() else None,
        "prototype": True
    }
