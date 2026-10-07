import { useEffect, useRef, useState } from 'react';
import { useChallenge } from '../hooks/useChallenge';
import { uploadEvidence } from '../services/api';
import LiveCapture from './LiveCapture';
import FinalDecision from './FinalDecision';

export default function ChallengeModal({ challengeId, onClose, onComplete }) {
  const dialogRef = useRef(null);
  const {
    challenge,
    loading,
    error,
    remainingSecs,
    verifyLive,
    verifySim
  } = useChallenge(challengeId);

  const [tab, setTab] = useState('live'); // 'live' | 'sim'
  const [isRecording, setIsRecording] = useState(false);
  const [partialText, setPartialText] = useState('');
  const [evidenceList, setEvidenceList] = useState([]);
  
  useEffect(() => {
    if (challengeId && dialogRef.current && !dialogRef.current.open) {
      dialogRef.current.showModal();
    }
  }, [challengeId]);

  const handleClose = () => {
    if (dialogRef.current) dialogRef.current.close();
    if (onClose) onClose();
  };

  const handleLiveComplete = async (videoBlob, audioBlob, finalText) => {
    if (loading || !challenge || challenge.status !== 'pending') return;
    setIsRecording(false);
    
    let evIds = [];
    let evObjects = [];
    try {
      if (videoBlob) {
        const ext = videoBlob.type.includes('mp4') ? 'mp4' : 'webm';
        const vidFile = new File([videoBlob], `challenge-${challengeId}-1.${ext}`, { type: videoBlob.type });
        const res = await uploadEvidence(vidFile);
        evIds.push(res.id);
        evObjects.push(res);
      }
      if (audioBlob) {
        const audFile = new File([audioBlob], `challenge-voice-${challengeId}-1.wav`, { type: 'audio/wav' });
        const res = await uploadEvidence(audFile);
        evIds.push(res.id);
        evObjects.push(res);
      }
    } catch (e) {
      console.error(e);
    }
    setEvidenceList(evObjects);
    
    const res = await verifyLive(finalText, evIds);
    if (res && res.status !== 'pending' && res.status !== 'retry') {
      if (onComplete) onComplete(res);
    }
  };

  const handleSimulate = async (outcome) => {
    const res = await verifySim(outcome);
    if (res && res.status !== 'pending' && res.status !== 'retry') {
      if (onComplete) onComplete(res);
    }
  };

  if (!challengeId) return null;

  const isResolved = challenge && (challenge.status === 'verified' || challenge.status === 'failed');

  return (
    <dialog ref={dialogRef} className="challenge-modal" onCancel={handleClose} aria-labelledby="challenge-dialog-title">
      <div className="challenge-modal-header">
        <h2 id="challenge-dialog-title">Verification Required</h2>
        <button className="btn-icon" onClick={handleClose} aria-label="Close">×</button>
      </div>

      <div className="challenge-modal-body">
        {error && <div className="error-box">{error}</div>}
        
        {!challenge ? (
          <div className="loading-state">Loading challenge...</div>
        ) : isResolved ? (
          <FinalDecision challenge={challenge} evidenceList={evidenceList} />
        ) : (
          <>
            <div className="challenge-instruction">
              <p className="instruction-text">{challenge.instruction}</p>
              
              <div className="challenge-meta">
                <span className={`timer ${remainingSecs <= 10 ? 'danger' : ''}`}>
                  {Math.floor(remainingSecs / 60)}:{(remainingSecs % 60).toString().padStart(2, '0')}
                </span>
                <span className="attempts">
                  Attempts left: {challenge.attempts_left}
                </span>
              </div>
            </div>
            
            <div className="tabs">
              <button 
                className={`tab ${tab === 'live' ? 'active' : ''}`}
                onClick={() => setTab('live')}
              >Live Test</button>
              <button 
                className={`tab ${tab === 'sim' ? 'active' : ''}`}
                onClick={() => setTab('sim')}
              >Simulate</button>
            </div>

            {tab === 'live' && (
              <div className="live-tab-content" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <LiveCapture 
                  onCapture={handleLiveComplete}
                />
              </div>
            )}

            {tab === 'sim' && (
              <div className="sim-tab-content" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <p>Use simulation to test the backend logic without speaking.</p>
                <div className="sim-buttons" style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn-secondary" onClick={() => handleSimulate('pass')} disabled={loading}>Pass</button>
                  <button className="btn-secondary" onClick={() => handleSimulate('unclear')} disabled={loading}>Unclear (Retry)</button>
                  <button className="btn-secondary danger" onClick={() => handleSimulate('fail')} disabled={loading}>Fail</button>
                </div>
              </div>
            )}
            
            {challenge.status === 'retry' && (
              <div className="retry-msg error-box" style={{ marginTop: '16px' }}>
                We couldn't clearly verify that. Please try again.
              </div>
            )}
            {challenge.expired && (
              <div className="error-box" style={{ marginTop: '16px' }}>
                Challenge expired. Please issue a new challenge.
              </div>
            )}
          </>
        )}
      </div>
    </dialog>
  );
}
