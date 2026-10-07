import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from PIL import Image
import numpy as np
import cv2
import wave
import pypdf

# Set temp dir before importing app/config
temp_dir = tempfile.TemporaryDirectory()
os.environ["TRUSTLOCK_DATA_DIR"] = temp_dir.name

from backend.main import app
from backend.storage import storage
from backend import evidence
from backend.config import MEDIA_RISK_CAP

@pytest.fixture(autouse=True)
def setup_db():
    storage.init_db()
    yield

client = TestClient(app)

def create_temp_jpeg():
    path = os.path.join(temp_dir.name, "test.jpg")
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(path, 'JPEG', quality=90)
    return path

def create_temp_wav():
    path = os.path.join(temp_dir.name, "test.wav")
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        # 1 second of silence
        wf.writeframes(np.zeros(44100, dtype=np.int16).tobytes())
    return path

def create_temp_mp4():
    path = os.path.join(temp_dir.name, "test.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, 20.0, (320, 240))
    for _ in range(20):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        out.write(frame)
    out.release()
    return path

def create_temp_pdf(text, producer=""):
    path = os.path.join(temp_dir.name, "test.pdf")
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(path)
    c.drawString(100, 100, text)
    c.save()
    
    if producer:
        writer = pypdf.PdfWriter()
        reader = pypdf.PdfReader(path)
        writer.append_pages_from_reader(reader)
        writer.add_metadata({"/Producer": producer})
        with open(path, "wb") as f:
            writer.write(f)
            
    return path

def test_jpeg_upload():
    path = create_temp_jpeg()
    with open(path, "rb") as f:
        response = client.post("/evidence", files={"files": ("test.jpg", f, "image/jpeg")})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["kind"] == "image"
    assert "sha256" in data["items"][0]

def test_wav_upload():
    path = create_temp_wav()
    with open(path, "rb") as f:
        response = client.post("/evidence", files={"files": ("test.wav", f, "audio/wav")})
    assert response.status_code == 200
    assert data["items"][0]["kind"] == "audio" if (data:=response.json()) else False

def test_mp4_upload():
    path = create_temp_mp4()
    with open(path, "rb") as f:
        response = client.post("/evidence", files={"files": ("test.mp4", f, "video/mp4")})
    assert response.status_code == 200

def test_pdf_name_matching():
    path = create_temp_pdf("Officer R. Menon", producer="Normal")
    with open(path, "rb") as f:
        response = client.post("/evidence", files={"files": ("test.pdf", f, "application/pdf")})
    
    assert response.status_code == 200
    ev_id = response.json()["items"][0]["id"]
    
    # Check find
    findings1 = evidence.collect_findings([ev_id], "R. Menon")
    assert findings1[0]["risk_hint"] == 0
    
    # Check not found
    findings2 = evidence.collect_findings([ev_id], "Arjun Nair")
    assert findings2[0]["risk_hint"] == 10

def test_pdf_producer_editing():
    path = create_temp_pdf("Some text", producer="Adobe Photoshop")
    with open(path, "rb") as f:
        response = client.post("/evidence", files={"files": ("test.pdf", f, "application/pdf")})
    
    ev_id = response.json()["items"][0]["id"]
    findings = evidence.collect_findings([ev_id], "Some text")
    assert findings[0]["risk_hint"] == 10

def test_risk_cap(monkeypatch):
    monkeypatch.setattr(evidence, "MEDIA_HINTS", {"editing_software": 50, "name_not_in_document": 50, "ela_high": 50, "pdf_date_mismatch": 50})
    path = create_temp_pdf("Missing", producer="Adobe Photoshop")
    with open(path, "rb") as f:
        response = client.post("/evidence", files={"files": ("test.pdf", f, "application/pdf")})
    ev_id = response.json()["items"][0]["id"]
    findings = evidence.collect_findings([ev_id], "John")
    assert findings[0]["risk_hint"] == 100 # collected risk is not capped here, the analyzer caps it
    
    # Let's test the analyzer cap
    from backend.analyzers.identity import analyze_identity
    from backend.schemas import IdentityInput
    inp = IdentityInput(claimed_name="John", claimed_role="Role", credential_verified=True, face_match=100, voice_match=100, liveness_ok=True)
    res = analyze_identity(inp, findings)
    assert res.sub_risk <= MEDIA_RISK_CAP

def test_rejections(monkeypatch):
    # 415 EXE as JPG
    path_exe = os.path.join(temp_dir.name, "bad.jpg")
    with open(path_exe, "wb") as f:
        f.write(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF\x00\x00\xB8\x00\x00\x00")
    with open(path_exe, "rb") as f:
        resp = client.post("/evidence", files={"files": ("bad.jpg", f, "image/jpeg")})
    assert resp.status_code == 415
    
    # 422 Corrupt JPG
    path_corrupt = os.path.join(temp_dir.name, "corrupt.jpg")
    with open(path_corrupt, "wb") as f:
        f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x00\x00\x00\x00\x00GARBAGE")
    with open(path_corrupt, "rb") as f:
        resp = client.post("/evidence", files={"files": ("corrupt.jpg", f, "image/jpeg")})
    assert resp.status_code == 422
    
    # 422 Empty
    path_empty = os.path.join(temp_dir.name, "empty.jpg")
    with open(path_empty, "wb") as f:
        pass
    with open(path_empty, "rb") as f:
        resp = client.post("/evidence", files={"files": ("empty.jpg", f, "image/jpeg")})
    assert resp.status_code == 422
    
    # 413 Oversize
    monkeypatch.setattr(evidence, "UPLOAD_LIMITS_MB", {"image": 0.0001})
    path = create_temp_jpeg()
    with open(path, "rb") as f:
        resp = client.post("/evidence", files={"files": ("test.jpg", f, "image/jpeg")})
    assert resp.status_code == 413

def test_get_file_and_range():
    path = create_temp_jpeg()
    with open(path, "rb") as f:
        original_bytes = f.read()
        f.seek(0)
        resp = client.post("/evidence", files={"files": ("test.jpg", f, "image/jpeg")})
        
    ev_id = resp.json()["items"][0]["id"]
    resp2 = client.get(f"/evidence/{ev_id}/file")
    assert resp2.status_code == 200
    assert resp2.content == original_bytes
    
    resp_range = client.get(f"/evidence/{ev_id}/file", headers={"Range": "bytes=0-9"})
    assert resp_range.status_code == 206
    assert len(resp_range.content) == 10

def test_delete_evidence():
    path = create_temp_jpeg()
    with open(path, "rb") as f:
        resp = client.post("/evidence", files={"files": ("test.jpg", f, "image/jpeg")})
    ev_id = resp.json()["items"][0]["id"]
    
    del_resp = client.delete(f"/evidence/{ev_id}")
    assert del_resp.status_code == 204
    
    assert client.get(f"/evidence/{ev_id}").status_code == 404
