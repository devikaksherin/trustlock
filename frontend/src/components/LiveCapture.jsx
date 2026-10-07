import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useSpeech } from '../hooks/useSpeech';
import { encodeWAV } from '../utils/wavRecorder';

export default function LiveCapture({ onCapture }) {
  const [browserInfo, setBrowserInfo] = useState('');
  const [deviceState, setDeviceState] = useState('initial'); // initial, checking, ok, error
  const [errorMsg, setErrorMsg] = useState('');
  const [brightnessError, setBrightnessError] = useState(false);
  const [cameras, setCameras] = useState([]);
  const [mics, setMics] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState('');
  const [selectedMic, setSelectedMic] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);

  const [recordState, setRecordState] = useState('idle'); // idle, recording, review
  const [timeLeft, setTimeLeft] = useState(8);
  const [reviewVideoUrl, setReviewVideoUrl] = useState('');
  const [reviewVideoBlob, setReviewVideoBlob] = useState(null);
  const [reviewAudioBlob, setReviewAudioBlob] = useState(null);

  const videoRef = useRef(null);
  const reviewVideoRef = useRef(null);
  const streamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const pcmChunksRef = useRef([]); // for wav
  const recordTimerRef = useRef(null);
  const micAnimRef = useRef(null);
  const processorRef = useRef(null);
  const sourceNodeRef = useRef(null);

  const { transcript, interim, error: speechError, startSpeech, stopSpeech } = useSpeech();

  // Browser checks
  useEffect(() => {
    let info = [];
    if (window.isSecureContext) info.push('Secure context: Yes');
    else info.push('Secure context: No');
    
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) info.push('Media Devices: Available');
    else info.push('Media Devices: Unavailable');
    
    const ua = navigator.userAgent;
    if (ua.includes('Electron') || ua.includes('Antigravity')) {
      info.push('Open this page in Chrome or Edge. Embedded browsers do not support camera and speech.');
    } else if (ua.includes('Firefox') || ua.includes('Brave')) {
      info.push('Browser: Firefox/Brave (Unsupported for speech)');
    } else {
      info.push('Browser: Chrome/Edge (Supported)');
    }
    setBrowserInfo(info.join(' | '));

    return () => {
      cleanupMedia();
    };
  }, []);

  const cleanupMedia = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      audioCtxRef.current.close().catch(console.error);
      audioCtxRef.current = null;
    }
    if (micAnimRef.current) {
      cancelAnimationFrame(micAnimRef.current);
    }
    if (recordTimerRef.current) clearInterval(recordTimerRef.current);
  };

  const getErrorMessage = (err) => {
    switch (err.name) {
      case 'NotAllowedError': return "Permission blocked. Click the lock icon in the address bar, allow camera and microphone, then retry.";
      case 'NotFoundError': return "No camera or microphone found.";
      case 'NotReadableError':
      case 'AbortError': return "Camera or microphone is in use by another app or browser tab (Teams, Zoom, Meet). Close it and retry.";
      case 'SecurityError': return "Camera needs https or http://localhost.";
      default: return err.message || "Unknown media error";
    }
  };

  const startStream = async (camId = null, micId = null) => {
    cleanupMedia();
    setDeviceState('checking');
    setErrorMsg('');
    setBrightnessError(false);

    let constraints = {
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 }
    };

    if (camId) constraints.video.deviceId = { exact: camId };
    if (micId) constraints.audio.deviceId = { exact: micId };

    try {
      await requestStream(constraints);
    } catch (err) {
      if (err.name === 'OverconstrainedError') {
        try {
          await requestStream({ video: true, audio: true });
        } catch (fallbackErr) {
          setErrorMsg(getErrorMessage(fallbackErr));
          setDeviceState('error');
        }
      } else {
        setErrorMsg(getErrorMessage(err));
        setDeviceState('error');
      }
    }
  };

  const requestStream = async (constraints) => {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia(constraints);
    } catch (e) {
      // Try one by one if both fails? The req says:
      // "if only one device fails continue with the other and say which is missing"
      // Since getUserMedia fails entirely if one is missing, we check:
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: constraints.video });
        setErrorMsg('Microphone is missing.');
      } catch (e2) {
        try {
          stream = await navigator.mediaDevices.getUserMedia({ audio: constraints.audio });
          setErrorMsg('Camera is missing.');
        } catch (e3) {
          throw e; // throw original
        }
      }
    }

    streamRef.current = stream;
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      await videoRef.current.play().catch(e => console.error("Play error:", e));
    }
    
    // Check brightness after 1.5s
    setTimeout(() => {
      if (videoRef.current && videoRef.current.videoWidth > 0) {
        checkBrightness(videoRef.current);
      }
    }, 1500);

    // Audio setup
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    const ctx = new AudioContext();
    audioCtxRef.current = ctx;

    const source = ctx.createMediaStreamSource(stream);
    sourceNodeRef.current = source;
    
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    analyserRef.current = analyser;
    
    updateMicLevel();
    enumerateDevices();
    setDeviceState('ok');
  };

  const enumerateDevices = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const c = devices.filter(d => d.kind === 'videoinput');
      const m = devices.filter(d => d.kind === 'audioinput');
      setCameras(c);
      setMics(m);
      if (!selectedCamera && c.length) setSelectedCamera(c[0].deviceId);
      if (!selectedMic && m.length) setSelectedMic(m[0].deviceId);
    } catch (e) {
      console.warn("enumerateDevices failed", e);
    }
  };

  const checkBrightness = (videoElement) => {
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let sum = 0;
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i], g = data[i+1], b = data[i+2];
      sum += (r + g + b) / 3;
    }
    const mean = sum / (data.length / 4);
    if (mean < 5) {
      setBrightnessError(true);
    }
  };

  const updateMicLevel = () => {
    if (!analyserRef.current) return;
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteTimeDomainData(dataArray);
    let sumSquares = 0;
    for (let i = 0; i < dataArray.length; i++) {
      const norm = (dataArray[i] / 128.0) - 1.0;
      sumSquares += norm * norm;
    }
    const rms = Math.sqrt(sumSquares / dataArray.length);
    setAudioLevel(rms * 100);
    micAnimRef.current = requestAnimationFrame(updateMicLevel);
  };

  // Recording
  const startRecording = async () => {
    if (audioCtxRef.current && audioCtxRef.current.state === 'suspended') {
      await audioCtxRef.current.resume();
    }
    
    setRecordState('recording');
    setTimeLeft(8);
    recordedChunksRef.current = [];
    pcmChunksRef.current = [];

    // Video recording
    const stream = streamRef.current;
    let mimeType = 'video/webm';
    const options = [
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp8,opus',
      'video/webm',
      'video/mp4'
    ];
    for (const opt of options) {
      if (MediaRecorder.isTypeSupported(opt)) {
        mimeType = opt;
        break;
      }
    }
    const recorder = new MediaRecorder(stream, { mimeType });
    mediaRecorderRef.current = recorder;
    
    recorder.ondataavailable = e => {
      if (e.data.size > 0) recordedChunksRef.current.push(e.data);
    };
    recorder.onstop = handleStopRecording;
    recorder.start(250);

    // Audio recording (ScriptProcessor fallback for simplicity instead of AudioWorklet blob)
    const ctx = audioCtxRef.current;
    const processor = ctx.createScriptProcessor(4096, 1, 1);
    processorRef.current = processor;
    
    processor.onaudioprocess = (e) => {
      const inputData = e.inputBuffer.getChannelData(0);
      const resampled = downsampleBuffer(inputData, ctx.sampleRate, 16000);
      pcmChunksRef.current.push(new Float32Array(resampled));
    };
    
    sourceNodeRef.current.connect(processor);
    processor.connect(ctx.destination); // Required for script processor to work, but we must ensure stream has echoCancellation or we don't connect to output. 
    // Wait, "Do NOT connect the mic to the speakers."
    // If we connect to destination, user hears themselves. To avoid this, we connect to a gain node with 0 volume, then destination.
    const zeroGain = ctx.createGain();
    zeroGain.gain.value = 0;
    processor.disconnect();
    processor.connect(zeroGain);
    zeroGain.connect(ctx.destination);
    
    startSpeech();

    recordTimerRef.current = setInterval(() => {
      setTimeLeft(t => {
        if (t <= 1) {
          stopRecording();
          return 0;
        }
        return t - 1;
      });
    }, 1000);
  };

  const downsampleBuffer = (buffer, sampleRate, outRate) => {
    if (outRate >= sampleRate) return buffer;
    const sampleRateRatio = sampleRate / outRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    let offsetResult = 0;
    let offsetBuffer = 0;
    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
      let accum = 0, count = 0;
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      result[offsetResult] = accum / count;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    return result;
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    if (processorRef.current) {
      processorRef.current.disconnect();
    }
    if (recordTimerRef.current) {
      clearInterval(recordTimerRef.current);
    }
    stopSpeech();
  };

  const handleStopRecording = () => {
    const videoBlob = new Blob(recordedChunksRef.current, { type: mediaRecorderRef.current.mimeType });
    setReviewVideoBlob(videoBlob);
    
    let totalLen = 0;
    for (const buf of pcmChunksRef.current) totalLen += buf.length;
    const merged = new Float32Array(totalLen);
    let offset = 0;
    for (const buf of pcmChunksRef.current) {
      merged.set(buf, offset);
      offset += buf.length;
    }
    
    const audioBlob = encodeWAV(merged, 16000);
    setReviewAudioBlob(audioBlob);

    const url = URL.createObjectURL(videoBlob);
    setReviewVideoUrl(url);
    setRecordState('review');
  };

  const handleUseRecording = () => {
    onCapture(reviewVideoBlob, reviewAudioBlob, transcript);
    if (reviewVideoUrl) URL.revokeObjectURL(reviewVideoUrl);
  };

  const handleRecordAgain = () => {
    if (reviewVideoUrl) URL.revokeObjectURL(reviewVideoUrl);
    setRecordState('idle');
  };

  const handleCameraChange = (e) => {
    setSelectedCamera(e.target.value);
    startStream(e.target.value, selectedMic);
  };

  const handleMicChange = (e) => {
    setSelectedMic(e.target.value);
    startStream(selectedCamera, e.target.value);
  };

  return (
    <div style={{ padding: '16px', background: 'var(--surface)', borderRadius: '8px', border: '1px solid var(--ink-4)' }}>
      <div style={{ fontSize: '0.8rem', color: 'var(--ink-2)', marginBottom: '8px' }}>{browserInfo}</div>
      
      {deviceState === 'initial' && (
        <button onClick={() => startStream()} className="button-primary">Check camera and microphone</button>
      )}

      {deviceState === 'checking' && <div>Checking devices...</div>}

      {deviceState === 'error' && (
        <div style={{ color: 'red', margin: '8px 0' }}>
          <strong>Error:</strong> {errorMsg}
        </div>
      )}

      {deviceState === 'ok' && recordState === 'idle' && (
        <div>
          {brightnessError && <div style={{ color: 'orange', marginBottom: '8px' }}>Camera opened but the picture is black (privacy shutter, or another app is using the camera)</div>}
          {errorMsg && <div style={{ color: 'orange', marginBottom: '8px' }}>{errorMsg}</div>}
          
          <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
            {cameras.length > 0 && (
              <select value={selectedCamera} onChange={handleCameraChange} style={{ flex: 1, padding: '4px' }}>
                {cameras.map(c => <option key={c.deviceId} value={c.deviceId}>{c.label || 'Camera'}</option>)}
              </select>
            )}
            {mics.length > 0 && (
              <select value={selectedMic} onChange={handleMicChange} style={{ flex: 1, padding: '4px' }}>
                {mics.map(m => <option key={m.deviceId} value={m.deviceId}>{m.label || 'Microphone'}</option>)}
              </select>
            )}
          </div>

          <video ref={videoRef} autoPlay playsInline muted style={{ width: '100%', maxHeight: '300px', objectFit: 'cover', transform: 'scaleX(-1)', background: '#000', borderRadius: '4px' }} />
          
          <div style={{ margin: '8px 0' }}>
            <div style={{ fontSize: '0.85rem', marginBottom: '4px' }}>Say something. The bar should move.</div>
            <div style={{ width: '100%', height: '10px', background: 'var(--ink-4)', borderRadius: '5px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${Math.min(100, audioLevel * 5)}%`, background: 'var(--brand)', transition: 'width 0.1s' }} />
            </div>
          </div>

          <button onClick={startRecording} className="button-primary" style={{ marginTop: '8px', width: '100%' }}>Record response</button>
        </div>
      )}

      {recordState === 'recording' && (
        <div>
          <video ref={videoRef} autoPlay playsInline muted style={{ width: '100%', maxHeight: '300px', objectFit: 'cover', transform: 'scaleX(-1)', background: '#000', borderRadius: '4px' }} />
          
          <div style={{ margin: '12px 0', textAlign: 'center', fontSize: '1.2rem', fontWeight: 'bold' }}>
            Recording... {timeLeft}s left
          </div>
          <div style={{ color: 'var(--ink-2)' }}>
            Transcript: {transcript} {interim && <span style={{ opacity: 0.7 }}>{interim}</span>}
          </div>
          {speechError && <div style={{ color: 'red', marginTop: '4px', fontSize: '0.9rem' }}>{speechError}</div>}
          
          <button onClick={stopRecording} className="button-secondary" style={{ marginTop: '8px', width: '100%' }}>Stop Early</button>
        </div>
      )}

      {recordState === 'review' && (
        <div>
          <video src={reviewVideoUrl} controls playsInline style={{ width: '100%', maxHeight: '300px', background: '#000', borderRadius: '4px' }} />
          <div style={{ margin: '8px 0', padding: '8px', background: 'var(--ink-4)', borderRadius: '4px' }}>
            <strong>Recognized Speech:</strong> {transcript || <span style={{ color: 'var(--ink-3)' }}>(No speech detected)</span>}
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <button onClick={handleRecordAgain} className="button-secondary" style={{ flex: 1 }}>Record again</button>
            <button onClick={handleUseRecording} className="button-primary" style={{ flex: 1 }}>Use this recording</button>
          </div>
        </div>
      )}
    </div>
  );
}
