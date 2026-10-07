import os
import requests
import time
import subprocess
import hashlib
import sys

from tests.test_evidence import create_temp_jpeg, create_temp_mp4, create_temp_wav, create_temp_pdf, temp_dir

def main():
    print("Starting uvicorn...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
        cwd=os.path.abspath(os.path.dirname(__file__))
    )
    time.sleep(3) # wait for startup
    
    try:
        jpeg = create_temp_jpeg()
        mp4 = create_temp_mp4()
        wav = create_temp_wav()
        pdf = create_temp_pdf("Officer R. Menon", producer="Normal")
        
        exe = os.path.join(temp_dir.name, "bad.jpg")
        with open(exe, "wb") as f:
            f.write(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF\x00\x00\xB8\x00\x00\x00")
            
        print("\n--- Uploading JPEG ---")
        with open(jpeg, "rb") as f:
            r = requests.post("http://localhost:8001/evidence", files={"files": ("test.jpg", f, "image/jpeg")})
            print(r.status_code, r.json())
            jpeg_id = r.json()["items"][0]["id"]
            
        print("\n--- Uploading MP4 ---")
        with open(mp4, "rb") as f:
            r = requests.post("http://localhost:8001/evidence", files={"files": ("test.mp4", f, "video/mp4")})
            print(r.status_code, r.json())
            
        print("\n--- Uploading WAV ---")
        with open(wav, "rb") as f:
            r = requests.post("http://localhost:8001/evidence", files={"files": ("test.wav", f, "audio/wav")})
            print(r.status_code, r.json())
            
        print("\n--- Uploading PDF ---")
        with open(pdf, "rb") as f:
            r = requests.post("http://localhost:8001/evidence", files={"files": ("test.pdf", f, "application/pdf")})
            print(r.status_code, r.json())
            
        print("\n--- GET /evidence/{id}/file for JPEG ---")
        with open(jpeg, "rb") as f:
            original_hash = hashlib.sha256(f.read()).hexdigest()
        r = requests.get(f"http://localhost:8001/evidence/{jpeg_id}/file")
        downloaded_hash = hashlib.sha256(r.content).hexdigest()
        print(f"Original hash: {original_hash}")
        print(f"Downloaded hash: {downloaded_hash}")
        print("Match?", original_hash == downloaded_hash)
        
        print("\n--- Uploading EXE disguised as JPG ---")
        with open(exe, "rb") as f:
            r = requests.post("http://localhost:8001/evidence", files={"files": ("bad.jpg", f, "image/jpeg")})
            print(r.status_code, r.json())
            
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
