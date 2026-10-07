import os
import cv2
import numpy as np
from PIL import Image, ExifTags
import mutagen
import wave

class UnreadableFile(Exception):
    pass

def classify_container(path: str) -> str:
    ext = path.split('.')[-1].lower() if '.' in path else ""
    if ext in ("ogg", "mp3", "wav"):
        return "audio"
    if ext in ("mp4", "mov", "m4a", "webm"):
        cap = cv2.VideoCapture(path)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            if ret:
                return "video"
        return "audio"
    return "unknown"

_face_cascade = None

def get_face_cascade():
    global _face_cascade
    if _face_cascade is None:
        if not hasattr(cv2, "CascadeClassifier"):
            return None
        _face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    return _face_cascade

def compute_sharpness(img_gray):
    return cv2.Laplacian(img_gray, cv2.CV_64F).var()

def count_faces(img_gray):
    cascade = get_face_cascade()
    if not cascade:
        return 0
    faces = cascade.detectMultiScale(img_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return len(faces)

def inspect_image(path: str):
    findings = []
    notes = []
    
    try:
        with Image.open(path) as img:
            format_name = img.format
            width, height = img.size
            findings.append({"key": "dimensions", "label": "Dimensions", "value": f"{width}x{height}", "source": "measured"})
            findings.append({"key": "format", "label": "Format", "value": format_name, "source": "measured"})
            
            exif = img.getexif()
            has_exif = bool(exif)
            findings.append({"key": "exif_present", "label": "EXIF Present", "value": "Yes" if has_exif else "No", "source": "measured"})
            
            if has_exif:
                exif_dict = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
                make = exif_dict.get("Make")
                model = exif_dict.get("Model")
                software = exif_dict.get("Software")
                if make or model:
                    findings.append({"key": "camera", "label": "Camera", "value": f"{make or ''} {model or ''}".strip(), "source": "measured"})
                if software:
                    findings.append({"key": "software", "label": "Software", "value": software, "source": "measured"})
            else:
                notes.append("No EXIF data found (often stripped by chat apps or screenshots).")

            # ELA
            if format_name == "JPEG":
                try:
                    import io
                    img_rgb = img.convert('RGB')
                    buffer = io.BytesIO()
                    img_rgb.save(buffer, 'JPEG', quality=90)
                    buffer.seek(0)
                    resaved = Image.open(buffer)
                    diff = np.abs(np.array(img_rgb, dtype=np.int16) - np.array(resaved, dtype=np.int16))
                    ela_mean = diff.mean()
                    findings.append({"key": "ela_score", "label": "ELA Score", "value": round(float(ela_mean), 2), "source": "measured", "detail": "compression inconsistency indicator"})
                except Exception as e:
                    notes.append(f"ELA failed: {str(e)}")
            elif format_name in ("PNG", "WEBP"):
                notes.append("ELA applies to JPEG only.")
                
        # OpenCV checks
        cv_img = cv2.imread(path)
        if cv_img is None:
            raise UnreadableFile("OpenCV failed to read image")
            
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        sharpness = compute_sharpness(gray)
        findings.append({"key": "sharpness", "label": "Sharpness", "value": round(sharpness, 1), "source": "measured"})
        
        faces = count_faces(gray)
        findings.append({"key": "face_count", "label": "Face Count", "value": faces, "source": "measured"})
        if faces == 0:
            notes.append("No face detected.")
        if sharpness < 100:
            notes.append("Image appears somewhat blurry.")
            
    except Exception as e:
        if isinstance(e, UnreadableFile):
            raise e
        raise UnreadableFile(str(e))
        
    return findings, notes

def inspect_video(path: str):
    findings = []
    notes = []
    
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise UnreadableFile("Cannot open video file")
        
    try:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        sharpness_list = []
        faces_found = 0
        face_counts = []
        
        if frame_count <= 0 or fps <= 0:
            frames_read = 0
            samples_to_keep = []
            while frames_read < 600:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                samples_to_keep.append(frame)
                frames_read += 1
                
            if frames_read == 0:
                raise UnreadableFile("Video has 0 readable frames")
                
            step = max(1, frames_read // 10)
            sampled_frames = samples_to_keep[::step][:10]
            
            duration_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
            duration = duration_msec / 1000.0 if duration_msec > 0 else 0
            if duration > 0:
                fps = frames_read / duration
            
            frame_count = frames_read
            if width == 0 and height == 0 and samples_to_keep:
                h, w = samples_to_keep[0].shape[:2]
                width, height = w, h
                
            for frame in sampled_frames:
                h, w = frame.shape[:2]
                if w > 640:
                    scale = 640 / w
                    frame = cv2.resize(frame, (640, int(h * scale)))
                    
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                sharpness_list.append(compute_sharpness(gray))
                fc = count_faces(gray)
                face_counts.append(fc)
                if fc > 0:
                    faces_found += 1
        else:
            duration = frame_count / fps if fps > 0 else 0
            
            samples = min(10, frame_count)
            indices = np.linspace(0, frame_count - 1, samples, dtype=int)
            
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue
                
                h, w = frame.shape[:2]
                if w > 640:
                    scale = 640 / w
                    frame = cv2.resize(frame, (640, int(h * scale)))
                    
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                sharpness_list.append(compute_sharpness(gray))
                fc = count_faces(gray)
                face_counts.append(fc)
                if fc > 0:
                    faces_found += 1
                    
        fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
        fourcc = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])
        
        findings.append({"key": "fps", "label": "FPS", "value": round(fps, 2), "source": "measured"})
        findings.append({"key": "frame_count", "label": "Frame Count", "value": frame_count, "source": "measured"})
        findings.append({"key": "duration", "label": "Duration (s)", "value": round(duration, 2), "source": "measured"})
        findings.append({"key": "resolution", "label": "Resolution", "value": f"{width}x{height}", "source": "measured"})
        findings.append({"key": "codec", "label": "Codec", "value": fourcc, "source": "measured"})

        if sharpness_list:
            findings.append({"key": "mean_sharpness", "label": "Mean Sharpness", "value": round(float(np.mean(sharpness_list)), 1), "source": "measured"})
            findings.append({"key": "face_ratio", "label": "Face Present Ratio", "value": f"{faces_found}/{len(sharpness_list)}", "source": "measured"})
            
            # Determine stable face count (avoiding single-frame false positives)
            if face_counts:
                multi_face_frames = sum(1 for c in face_counts if c > 1)
                # If multiple faces appear in >= 20% of sampled frames (e.g., 2 out of 10)
                if multi_face_frames >= max(1, len(face_counts) * 0.2):
                    stable_face_count = max(face_counts)
                elif faces_found >= max(1, len(face_counts) * 0.2):
                    stable_face_count = 1
                else:
                    stable_face_count = 0
                    
                findings.append({"key": "face_count", "label": "Face Count", "value": stable_face_count, "source": "measured"})
            
    finally:
        cap.release()
        
    return findings, notes

def inspect_audio(path: str):
    findings = []
    notes = []
    
    try:
        f = mutagen.File(path)
        if f is None:
            raise UnreadableFile("Mutagen could not read audio file")
            
        info = f.info
        duration = getattr(info, "length", 0)
        sample_rate = getattr(info, "sample_rate", 0)
        channels = getattr(info, "channels", 0)
        bitrate = getattr(info, "bitrate", 0)
        
        findings.append({"key": "duration", "label": "Duration (s)", "value": round(duration, 2), "source": "measured"})
        if sample_rate: findings.append({"key": "sample_rate", "label": "Sample Rate (Hz)", "value": sample_rate, "source": "measured"})
        if channels: findings.append({"key": "channels", "label": "Channels", "value": channels, "source": "measured"})
        if bitrate: findings.append({"key": "bitrate", "label": "Bitrate (bps)", "value": bitrate, "source": "measured"})
        
        if path.lower().endswith(".wav"):
            try:
                import struct
                with open(path, 'rb') as f:
                    riff = f.read(4)
                    if riff != b'RIFF':
                        raise ValueError("Not a RIFF file")
                    f.read(4)
                    if f.read(4) != b'WAVE':
                        raise ValueError("Not a WAVE file")
                    
                    fmt_chunk = False
                    data_chunk = False
                    channels, sample_rate, bit_depth = 0, 0, 0
                    format_tag = 0
                    audio_data = b''
                    
                    while True:
                        chunk_header = f.read(8)
                        if len(chunk_header) < 8:
                            break
                        chunk_id, chunk_size = struct.unpack('<4sI', chunk_header)
                        
                        if chunk_id == b'fmt ':
                            fmt_data = f.read(chunk_size)
                            format_tag, channels, sample_rate, avg_bytes_per_sec, block_align, bit_depth = struct.unpack('<HHIIHH', fmt_data[:16])
                            fmt_chunk = True
                        elif chunk_id == b'data':
                            audio_data = f.read(chunk_size)
                            data_chunk = True
                            break
                        else:
                            f.read(chunk_size)
                            
                    if not fmt_chunk or not data_chunk:
                        raise ValueError("Missing fmt or data chunk")
                        
                    nframes = len(audio_data) // (channels * (bit_depth // 8))
                    
                    if bit_depth == 8:
                        arr = np.frombuffer(audio_data, dtype=np.uint8).astype(np.float32) - 128.0
                        max_val = 128.0
                    elif bit_depth == 16:
                        arr = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
                        max_val = 32768.0
                    elif bit_depth == 24:
                        a = np.empty((len(audio_data) // 3, 4), dtype=np.uint8)
                        a[:, 0] = 0
                        a[:, 1::] = np.frombuffer(audio_data, dtype=np.uint8).reshape(-1, 3)
                        arr = a.view('<i4').reshape(-1).astype(np.float32) / 256.0
                        max_val = 8388608.0
                    elif bit_depth == 32:
                        if format_tag == 3 or (format_tag == 0xFFFE and len(fmt_data) >= 26 and fmt_data[24:26] == b'\x03\x00'):
                            arr = np.frombuffer(audio_data, dtype=np.float32)
                            max_val = 1.0
                        else:
                            arr = np.frombuffer(audio_data, dtype=np.int32).astype(np.float32)
                            max_val = 2147483648.0
                    else:
                        raise ValueError(f"Unsupported bit depth: {bit_depth}")
                        
                    window_size = int(sample_rate * 0.05) * channels
                    if window_size > 0:
                        num_windows = len(arr) // window_size
                        if num_windows > 0:
                            reshaped = arr[:num_windows * window_size].reshape(num_windows, window_size)
                            rms_per_window = np.sqrt(np.mean(reshaped**2, axis=1))
                            mean_rms = float(np.mean(rms_per_window))
                            
                            if mean_rms > 0:
                                dbfs = 20 * np.log10(mean_rms / max_val)
                            else:
                                dbfs = -100.0
                                
                            silence_thresh = 0.01 * max_val
                            silent_windows = np.sum(rms_per_window < silence_thresh)
                            silence_ratio = float(silent_windows / num_windows)
                            
                            findings.append({"key": "rms_level", "label": "Mean RMS (dBFS)", "value": round(dbfs, 2), "source": "measured"})
                            findings.append({"key": "silence_ratio", "label": "Silence Ratio", "value": round(silence_ratio, 3), "source": "measured"})
            except Exception as e:
                notes.append(f"WAV detailed analysis skipped: {str(e)}")
                
    except Exception as e:
        if isinstance(e, UnreadableFile):
            raise e
        raise UnreadableFile(str(e))
        
    return findings, notes
