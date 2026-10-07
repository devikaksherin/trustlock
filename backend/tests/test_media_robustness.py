import pytest
import cv2
import struct
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app
from backend.analyzers.media import inspect_audio, inspect_video, classify_container, UnreadableFile

client = TestClient(app)

def generate_wav(path, bit_depth, extensible=False):
    import wave
    with open(path, 'wb') as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + 8))
        f.write(b'WAVE')
        f.write(b'fmt ')
        if extensible:
            f.write(struct.pack('<I', 40))
            f.write(struct.pack('<HHIIHH', 0xFFFE, 1, 16000, 16000 * (bit_depth//8), bit_depth//8, bit_depth))
            f.write(struct.pack('<H', 22))
            f.write(struct.pack('<H', bit_depth))
            f.write(struct.pack('<I', 4))
            f.write(b'\x03\x00\x00\x00\x00\x00\x10\x00\x80\x00\x00\xAA\x00\x38\x9B\x71')
        elif bit_depth == 32:
            f.write(struct.pack('<I', 16))
            f.write(struct.pack('<HHIIHH', 3, 1, 16000, 16000 * 4, 4, 32))
        else:
            f.write(struct.pack('<I', 16))
            f.write(struct.pack('<HHIIHH', 1, 1, 16000, 16000 * (bit_depth//8), bit_depth//8, bit_depth))
            
        f.write(b'data')
        data_len = 16000 * (bit_depth // 8)
        f.write(struct.pack('<I', data_len))
        f.write(b'\x00' * data_len)

def test_inspect_audio_float32_wav(tmp_path):
    path = str(tmp_path / "test.wav")
    generate_wav(path, 32, extensible=False)
    findings, notes = inspect_audio(path)
    assert any(f["key"] == "rms_level" for f in findings)
    
def test_inspect_audio_extensible_wav(tmp_path):
    path = str(tmp_path / "test2.wav")
    generate_wav(path, 32, extensible=True)
    findings, notes = inspect_audio(path)
    assert any(f["key"] == "rms_level" for f in findings)

def test_classify_container(monkeypatch):
    class DummyVideoCap:
        def __init__(self, path):
            self.opened = path.endswith('good.mp4')
        def isOpened(self):
            return self.opened
        def read(self):
            return True, None
        def release(self):
            pass

    monkeypatch.setattr(cv2, "VideoCapture", DummyVideoCap)
    assert classify_container("test.ogg") == "audio"
    assert classify_container("good.mp4") == "video"
    assert classify_container("bad.webm") == "audio"

def test_inspect_video_fallback(monkeypatch, tmp_path):
    class DummyVideoCap:
        def __init__(self, path):
            self.read_count = 0
        def isOpened(self):
            return True
        def get(self, propId):
            if propId == cv2.CAP_PROP_FRAME_COUNT: return 0
            if propId == cv2.CAP_PROP_FPS: return 30.0
            if propId == cv2.CAP_PROP_FRAME_WIDTH: return 640
            if propId == cv2.CAP_PROP_FRAME_HEIGHT: return 480
            if propId == cv2.CAP_PROP_POS_MSEC: return 1000.0
            return 0
        def set(self, propId, val): pass
        def read(self):
            if self.read_count < 15:
                import numpy as np
                self.read_count += 1
                return True, np.zeros((480, 640, 3), dtype=np.uint8)
            return False, None
        def release(self): pass

    monkeypatch.setattr(cv2, "VideoCapture", DummyVideoCap)
    path = str(tmp_path / "dummy.webm")
    with open(path, "w") as f: f.write("dummy")
    findings, notes = inspect_video(path)
    assert any(f["key"] == "face_ratio" for f in findings)
    assert any(f["key"] == "duration" for f in findings)

def test_evidence_decode_failure_stored(monkeypatch, tmp_path):
    class DummyVideoCap:
        def __init__(self, path): pass
        def isOpened(self): return True
        def get(self, propId): return 0
        def set(self, propId, val): pass
        def read(self): return False, None
        def release(self): pass

    monkeypatch.setattr(cv2, "VideoCapture", DummyVideoCap)
    
    path = str(tmp_path / "fail.mp4")
    with open(path, "wb") as f: f.write(b"not a real mp4 but we bypass type check")
    
    import filetype
    class DummyKind:
        def __init__(self):
            self.extension = "mp4"
            self.mime = "video/mp4"
    def dummy_guess(p): return DummyKind()
    monkeypatch.setattr(filetype, "guess", dummy_guess)
    
    with open(path, "rb") as f:
        resp = client.post("/evidence", files=[("files", ("fail.mp4", f, "video/mp4"))])
    
    assert resp.status_code == 200
    ev_id = resp.json()["items"][0]["id"]
    
    ev_resp = client.get(f"/evidence/{ev_id}")
    assert ev_resp.status_code == 200
    assert "Could not decode frames/metadata for analysis" in str(ev_resp.json()["notes"])
    
def test_audio_range_request(tmp_path, monkeypatch):
    import filetype
    class DummyKind:
        def __init__(self):
            self.extension = "wav"
            self.mime = "audio/wav"
    def dummy_guess(p): return DummyKind()
    monkeypatch.setattr(filetype, "guess", dummy_guess)

    path = str(tmp_path / "test.wav")
    with open(path, "wb") as f: f.write(b"0123456789")
    
    with open(path, "rb") as f:
        resp = client.post("/evidence", files=[("files", ("test.wav", f, "audio/wav"))])
        
    ev_id = resp.json()["items"][0]["id"]
    
    range_resp = client.get(f"/evidence/{ev_id}/file", headers={"Range": "bytes=2-5"})
    assert range_resp.status_code == 206
    assert range_resp.headers["Content-Length"] == "4"
    assert range_resp.content == b"2345"
