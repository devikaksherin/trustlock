import { useState, useRef, useCallback } from 'react';

export function useSpeech() {
  const [transcript, setTranscript] = useState('');
  const [interim, setInterim] = useState('');
  const [error, setError] = useState(null);
  const recognitionRef = useRef(null);

  const startSpeech = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError("Speech recognition is not supported in this browser.");
      return;
    }
    
    setError(null);
    setTranscript('');
    setInterim('');
    
    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = 'en-IN'; // Will fallback to default if not supported
    
    rec.onerror = (e) => {
      let msg = 'Microphone error: ' + e.error;
      if (e.error === 'not-allowed') msg = "Speech recognition permission blocked.";
      if (e.error === 'service-not-allowed') msg = "Speech service is not allowed.";
      if (e.error === 'no-speech') msg = "No speech detected. Check the mic level bar.";
      if (e.error === 'audio-capture') msg = "Audio capture failed.";
      if (e.error === 'network') msg = "The browser speech service needs an internet connection.";
      setError(msg);
    };

    rec.onresult = (e) => {
      let finalStr = '';
      let interimStr = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalStr += t + ' ';
        else interimStr += t;
      }
      if (finalStr.trim()) setTranscript(prev => (prev + ' ' + finalStr.trim()).trim());
      setInterim(interimStr.trim());
    };

    try {
      rec.start();
      recognitionRef.current = rec;
    } catch (e) {
      console.warn("Failed to start speech recognition", e);
    }
  }, []);

  const stopSpeech = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
  }, []);

  return { transcript, interim, error, startSpeech, stopSpeech };
}
