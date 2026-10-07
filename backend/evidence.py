import os
import uuid
import hashlib
from datetime import datetime, timezone
import string
import filetype
from fastapi import UploadFile, HTTPException

from .config import UPLOAD_DIR, ALLOWED_TYPES, UPLOAD_LIMITS_MB, EDITING_SOFTWARE, ELA_MEAN_THRESHOLD, MEDIA_HINTS
from .storage import storage
from .analyzers.media import inspect_image, inspect_video, inspect_audio, UnreadableFile, classify_container
from .analyzers.document import inspect_document

def sanitize_filename(name: str) -> str:
    if not name:
        return "unnamed"
    name = os.path.basename(name)
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    sanitized = ''.join(c for c in name if c in valid_chars)
    return sanitized[:100] or "unnamed"

def detect_kind_from_ext(ext: str):
    ext = ext.lower()
    for kind, exts in ALLOWED_TYPES.items():
        if ext in exts:
            return kind
    return None

async def save_upload(upload: UploadFile):
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
        
    original_name = sanitize_filename(upload.filename)
    ext = original_name.split('.')[-1].lower() if '.' in original_name else ""
    kind_hint = detect_kind_from_ext(ext)
    
    file_id = str(uuid.uuid4())
    stored_name = f"{file_id}.{ext}" if ext else file_id
    path = os.path.join(UPLOAD_DIR, stored_name)
    
    sha256 = hashlib.sha256()
    size = 0
    limit_bytes = (UPLOAD_LIMITS_MB.get(kind_hint) or 20) * 1024 * 1024
    
    with open(path, "wb") as out:
        while True:
            chunk = await upload.read(65536)
            if not chunk:
                break
            size += len(chunk)
            if size > limit_bytes:
                out.close()
                os.remove(path)
                raise HTTPException(status_code=413, detail="file_too_large")
            sha256.update(chunk)
            out.write(chunk)
            
    if size == 0:
        os.remove(path)
        raise HTTPException(status_code=422, detail="empty_file")
        
    kind = filetype.guess(path)
    mime = kind.mime if kind else None
    
    if mime:
        real_ext = kind.extension
        real_kind = detect_kind_from_ext(real_ext)
        if real_kind in ("audio", "video"):
            real_kind = classify_container(path)
            if real_kind == "audio":
                if ext == "m4a": mime = "audio/mp4"
                elif ext == "webm": mime = "audio/webm"
                elif ext == "ogg": mime = "audio/ogg"
                elif ext == "wav": mime = "audio/wav"
                elif ext == "mp3": mime = "audio/mpeg"
    else:
        # Fallback for txt
        if ext == "txt":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    f.read(1024)
                real_kind = "document"
                mime = "text/plain"
            except UnicodeDecodeError:
                os.remove(path)
                raise HTTPException(status_code=415, detail="unsupported_type")
        else:
            os.remove(path)
            raise HTTPException(status_code=415, detail="unsupported_type")
            
    if not real_kind:
        os.remove(path)
        raise HTTPException(status_code=415, detail="unsupported_type")
        
    findings = []
    notes = []
    extracted_text = ""
    
    try:
        if real_kind == "image":
            findings, notes = inspect_image(path)
        elif real_kind == "video":
            findings, notes = inspect_video(path)
        elif real_kind == "audio":
            findings, notes = inspect_audio(path)
        elif real_kind == "document":
            findings, notes, extracted_text = inspect_document(path, ext)
    except UnreadableFile as e:
        if real_kind in ("audio", "video"):
            notes.append("Could not decode frames/metadata for analysis. The file is stored and may still play in the browser.")
        else:
            print(f"UnreadableFile Error: {e}")
            os.remove(path)
            raise HTTPException(status_code=422, detail="unreadable_file")
        
    record = {
        "id": file_id,
        "original_name": original_name,
        "stored_name": stored_name,
        "kind": real_kind,
        "mime": mime,
        "ext": ext,
        "size_bytes": size,
        "sha256": sha256.hexdigest(),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "findings": findings,
        "notes": notes,
        "extracted_text": extracted_text
    }
    
    storage.save_evidence(record)
    
    return {
        "id": record["id"],
        "original_name": record["original_name"],
        "kind": record["kind"],
        "mime": record["mime"],
        "size_bytes": record["size_bytes"],
        "sha256": record["sha256"],
        "uploaded_at": record["uploaded_at"]
    }

def get_evidence(id: str):
    return storage.get_evidence(id)

def delete_evidence(id: str):
    ev = storage.get_evidence(id)
    if ev:
        path = os.path.join(UPLOAD_DIR, ev["stored_name"])
        if os.path.exists(path):
            os.remove(path)
        storage.delete_evidence(id)

def _contains_editing_software(s: str) -> bool:
    if not s: return False
    s_lower = s.lower()
    return any(es in s_lower for es in EDITING_SOFTWARE)

def collect_findings(evidence_ids: list[str], claimed_name: str) -> list[dict]:
    results = []
    if not claimed_name: claimed_name = ""
    
    name_tokens = [t.strip(string.punctuation).lower() for t in claimed_name.split() if len(t.strip(string.punctuation)) >= 2]
    
    for eid in evidence_ids:
        ev = get_evidence(eid)
        if not ev:
            continue
            
        risk_hint = 0
        findings = ev.get("findings", [])
        notes = ev.get("notes", [])
        extracted_text = ev.get("extracted_text", "")
        kind = ev["kind"]
        
        if kind == "image":
            for f in findings:
                if f["key"] == "software" and _contains_editing_software(f["value"]):
                    risk_hint += MEDIA_HINTS["editing_software"]
                if f["key"] == "ela_score" and float(f["value"]) > ELA_MEAN_THRESHOLD:
                    risk_hint += MEDIA_HINTS["ela_high"]
        elif kind == "document" and ev["mime"] == "application/pdf":
            producer_or_creator = ""
            c_date = None
            m_date = None
            text_extractable = False
            for f in findings:
                if f["key"] in ("producer", "creator"):
                    producer_or_creator += " " + f["value"]
                if f["key"] == "creation_date":
                    c_date = datetime.fromisoformat(f["value"])
                if f["key"] == "mod_date":
                    m_date = datetime.fromisoformat(f["value"])
                if f["key"] == "text_extractable" and f["value"] == "Yes":
                    text_extractable = True
                    
            if _contains_editing_software(producer_or_creator):
                risk_hint += MEDIA_HINTS["editing_software"]
                
            if c_date and m_date:
                diff = m_date - c_date
                if diff.total_seconds() > 86400: # 1 day
                    risk_hint += MEDIA_HINTS["pdf_date_mismatch"]
                    
            if claimed_name and text_extractable:
                text_lower = extracted_text.lower()
                all_found = all(t in text_lower for t in name_tokens) if name_tokens else True
                if not all_found:
                    risk_hint += MEDIA_HINTS["name_not_in_document"]
                findings.append({"key": "name_match", "label": "Claimed Name Found", "value": "Yes" if all_found else "No", "source": "measured"})
                
        elif kind == "document" and ev["mime"] == "text/plain":
            if claimed_name:
                text_lower = extracted_text.lower()
                all_found = all(t in text_lower for t in name_tokens) if name_tokens else True
                if not all_found:
                    risk_hint += MEDIA_HINTS["name_not_in_document"]
                findings.append({"key": "name_match", "label": "Claimed Name Found", "value": "Yes" if all_found else "No", "source": "measured"})
                
        results.append({
            "id": eid,
            "original_name": ev["original_name"],
            "kind": kind,
            "sha256": ev["sha256"],
            "findings": findings,
            "notes": notes,
            "risk_hint": risk_hint
        })
        
    return results
