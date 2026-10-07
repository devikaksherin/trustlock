import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Response
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime, timezone

from .config import WEIGHTS, THRESHOLDS, HIGH_VALUE_INR, CONFIG_VERSION, UPLOAD_DIR
from .storage import storage, ledger_lock
from . import evidence
from . import challenge
from . import risk_engine
from .scenarios import SCENARIOS
from .schemas import (
    ChallengeGenerateRequest, ChallengeGenerateResponse,
    ChallengeVerifyRequest, ChallengeVerifyResponse,
    ChallengeViewResponse,
    AnalyzeRequest, AnalyzeResponse,
    Profile
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    storage.init_db()
    print("TRUSTLOCK API ready on http://127.0.0.1:8001 (docs: /docs)")
    yield

app = FastAPI(title="TRUSTLOCK API", lifespan=lifespan)

origins = os.environ.get("TRUSTLOCK_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
    max_age=600,
    expose_headers=["Content-Range", "Accept-Ranges", "Content-Length", "Content-Disposition"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(
        status_code=500,
        content={"error": "server_error", "detail": str(exc)}
    )

@app.get("/")
def root():
    return {"service": "TRUSTLOCK API", "version": CONFIG_VERSION}

@app.get("/health")
def health():
    status = "ok"
    try:
        import sqlite3
        conn = sqlite3.connect(storage.db_path)
        conn.execute("SELECT 1").fetchall()
        conn.close()
        
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR, exist_ok=True)
        test_file = os.path.join(UPLOAD_DIR, ".health_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        storage_status = "ok"
    except Exception as e:
        status = "degraded"
        storage_status = "error"

    return {
        "status": status,
        "service": "trustlock",
        "version": CONFIG_VERSION,
        "time": datetime.now(timezone.utc).isoformat(),
        "storage": storage_status
    }

@app.get("/config")
def get_config():
    return {
        "weights": WEIGHTS,
        "thresholds": THRESHOLDS,
        "high_value_inr": HIGH_VALUE_INR,
        "config_version": CONFIG_VERSION
    }

@app.get("/profiles", response_model=List[Profile])
def get_profiles():
    return storage.list_profiles()

@app.post("/profiles")
def save_profile(profile: Profile):
    storage.save_profile(profile.model_dump())
    return {"status": "ok"}

@app.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str):
    storage.delete_profile(profile_id)
    return Response(status_code=204)


@app.post("/evidence")
async def upload_evidence(files: List[UploadFile] = File(...)):
    items = []
    errors = []
    for f in files:
        try:
            res = await evidence.save_upload(f)
            items.append(res)
        except HTTPException as e:
            errors.append({"filename": f.filename, "error": e.detail, "detail": str(e.detail)})
        except Exception as e:
            errors.append({"filename": f.filename, "error": "unknown_error", "detail": str(e)})
            
    if not items and errors:
        first_err = errors[0]["error"]
        status_code = 422
        if first_err == "file_too_large": status_code = 413
        elif first_err == "unsupported_type": status_code = 415
        raise HTTPException(status_code=status_code, detail=first_err)
        
    return {"items": items, "errors": errors}

@app.get("/evidence/{id}")
def get_evidence_endpoint(id: str):
    ev = evidence.get_evidence(id)
    if not ev:
        raise HTTPException(status_code=404, detail="not_found")
    # Return record without extracted_text
    ev.pop("extracted_text", None)
    ev.pop("findings_json", None)
    ev.pop("notes_json", None)
    return ev

@app.get("/evidence/{id}/file")
def get_evidence_file(id: str, request: Request):
    ev = evidence.get_evidence(id)
    if not ev:
        raise HTTPException(status_code=404, detail="not_found")
    path = os.path.join(UPLOAD_DIR, ev["stored_name"])
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="not_found")
        
    file_size = os.path.getsize(path)
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": "inline",
        "X-Content-Type-Options": "nosniff"
    }
    
    range_header = request.headers.get("range")
    if range_header and range_header.startswith("bytes="):
        try:
            byte_range = range_header.replace("bytes=", "").split("-")
            start = int(byte_range[0])
            end = int(byte_range[1]) if byte_range[1] else file_size - 1
            if start >= file_size or end >= file_size:
                raise HTTPException(status_code=416, detail="range_not_satisfiable")
            
            chunk_size = end - start + 1
            headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            headers["Content-Length"] = str(chunk_size)
            
            def file_chunk_generator():
                with open(path, "rb") as f:
                    f.seek(start)
                    bytes_to_read = chunk_size
                    while bytes_to_read > 0:
                        chunk = f.read(min(65536, bytes_to_read))
                        if not chunk:
                            break
                        bytes_to_read -= len(chunk)
                        yield chunk
                        
            return StreamingResponse(
                file_chunk_generator(),
                status_code=206,
                media_type=ev["mime"],
                headers=headers
            )
        except ValueError:
            pass
            
    headers["Content-Length"] = str(file_size)
    return FileResponse(
        path,
        media_type=ev["mime"],
        headers=headers
    )

@app.delete("/evidence/{id}")
def delete_evidence_endpoint(id: str):
    evidence.delete_evidence(id)
    return Response(status_code=204)


@app.post("/challenge/generate", response_model=ChallengeGenerateResponse)
def api_generate_challenge(req: ChallengeGenerateRequest):
    try:
        return challenge.generate_challenge(req.case_id, req.decision)
    except ValueError as e:
        if str(e) == "no challenge needed":
            raise HTTPException(status_code=422, detail="no_challenge_needed")
        raise e

@app.post("/challenge/verify", response_model=ChallengeVerifyResponse)
def api_verify_challenge(req: ChallengeVerifyRequest):
    try:
        return challenge.verify_challenge(
            challenge_id=req.challenge_id,
            response=req.response,
            simulation=req.simulation,
            simulated_outcome=req.simulated_outcome,
            evidence_ids=req.evidence_ids
        )
    except challenge.NotFound:
        raise HTTPException(status_code=404, detail="not_found")
    except challenge.Closed:
        raise HTTPException(status_code=409, detail="challenge_closed")
    except challenge.ValidationError as e:
        if str(e) == "invalid simulated_outcome":
            raise HTTPException(status_code=422, detail="invalid_simulation")
        raise HTTPException(status_code=422, detail=str(e))

@app.get("/challenge/{challenge_id}", response_model=ChallengeViewResponse)
def get_challenge_view(challenge_id: str):
    ch = storage.get_challenge(challenge_id)
    if not ch:
        raise HTTPException(status_code=404, detail="not_found")
    
    expires_at = challenge.datetime.fromisoformat(ch["expires_at"])
    now = challenge.now()
    remaining = int((expires_at - now).total_seconds())
    if remaining < 0:
        remaining = 0
        
    return {
        "challenge_id": ch["id"],
        "case_id": ch["case_id"],
        "type": ch["type"],
        "instruction": ch["instruction"],
        "status": ch["status"],
        "attempts_left": ch["attempts_left"],
        "ttl_seconds": challenge.CHALLENGE_TTL_SECONDS,
        "remaining_seconds": remaining,
        "expired": remaining == 0,
        "expires_at": ch["expires_at"],
        "final_decision": ch.get("final_decision"),
        "human_review": ch.get("human_review", False),
        "final_note": ch.get("final_note"),
        "prototype": True
    }

@app.get("/scenarios")
def get_scenarios():
    return SCENARIOS

@app.post("/analyze", response_model=AnalyzeResponse)
def api_analyze(req: AnalyzeRequest):
    if req.scenario_id:
        if not any(s["id"] == req.scenario_id for s in SCENARIOS):
            raise HTTPException(status_code=422, detail="unknown_scenario")
            
    scenario = next((s for s in SCENARIOS if s["id"] == req.scenario_id), None)
    
    with ledger_lock:
        case_id = storage.next_case_id()
        findings = evidence.collect_findings(req.evidence_ids, req.identity.claimed_name)
        
        profile_data = None
        if req.profile_id:
            profile_data = storage.get_profile(req.profile_id)
            
        response = risk_engine.analyze(req, findings, case_id, profile_data)
        
        if response.decision in ("VERIFY", "BLOCK"):
            ch_data = challenge.generate_challenge(case_id, response.decision)
            response.challenge_id = ch_data["challenge_id"]
            
        top_reason = "No risk signals flagged"
        for r in response.reasons:
            if r.severity != "pass":
                top_reason = r.title
                break
                
        payload = response.model_dump()
        payload.update({
            "identity": req.identity.model_dump(),
            "context": req.context.model_dump(),
            "behavior": req.behavior.model_dump(),
            "transaction": req.transaction.model_dump(),
            "scenario_id": req.scenario_id,
            "scenario_title": scenario["title"] if scenario else None,
            "top_reason": top_reason
        })
        
        storage.append_event("ANALYSIS", case_id, payload)
        
    return response

@app.get("/history/verify")
def api_history_verify():
    return storage.verify_chain()

@app.get("/history/{case_id}")
def get_history_case(case_id: str):
    events = storage.get_case(case_id)
    if not events:
        raise HTTPException(status_code=404, detail="not_found")
        
    analysis_payload = None
    challenges = []
    
    for ev in events:
        import json
        p = json.loads(ev["payload_json"])
        if ev["event_type"] == "ANALYSIS":
            analysis_payload = p
        elif ev["event_type"] == "CHALLENGE_RESULT":
            ch = {
                "record_hash": ev["record_hash"],
                "prev_hash": ev["prev_hash"],
                "outcome": p.get("outcome"),
                "final_decision": p.get("final_decision"),
                "human_review": p.get("human_review"),
                "final_note": p.get("final_note"),
                "checks": p.get("checks")
            }
            challenges.append(ch)
            
    if not analysis_payload:
        raise HTTPException(status_code=404, detail="not_found")
        
    return {
        "analysis": analysis_payload,
        "challenges": challenges
    }

@app.get("/history")
def list_history(decision: str = "all", limit: int = 50, offset: int = 0):
    limit = min(limit, 200)
    cases, total = storage.list_cases(decision, limit, offset)
    
    items = []
    import json
    for row in cases:
        p = json.loads(row["payload_json"])
        case_id = p["case_id"]
        
        # Get latest challenge result for this case
        all_events = storage.get_case(case_id)
        challenge_info = None
        eff_dec = p["decision"]
        
        for ev in reversed(all_events):
            if ev["event_type"] == "CHALLENGE_RESULT":
                cp = json.loads(ev["payload_json"])
                challenge_info = {
                    "outcome": cp.get("outcome"),
                    "final_decision": cp.get("final_decision"),
                    "human_review": cp.get("human_review", False),
                    "final_note": cp.get("final_note")
                }
                if cp.get("final_decision"):
                    eff_dec = cp.get("final_decision")
                break
                
        items.append({
            "case_id": case_id,
            "timestamp": p["timestamp"],
            "scenario_id": p.get("scenario_id"),
            "scenario_title": p.get("scenario_title"),
            "trust_score": p["trust_score"],
            "risk_level": p["risk_level"],
            "decision": p["decision"],
            "top_reason": p.get("top_reason"),
            "challenge_id": p.get("challenge_id"),
            "challenge": challenge_info,
            "effective_decision": eff_dec,
            "evidence_count": len(p.get("evidence", [])),
            "record_hash_prefix": row["record_hash"][:12]
        })
        
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.delete("/history")
def delete_history(confirm: str = "false"):
    if confirm.lower() != "true":
        raise HTTPException(status_code=400, detail="confirmation_required")
    storage.reset_ledger()
    return Response(status_code=204)


