import EvidenceCard from './EvidenceCard';

export default function FinalDecision({ challenge, evidenceList = [] }) {
  if (!challenge) return null;
  
  const isPass = challenge.final_decision === 'ALLOW';
  const isBlock = challenge.final_decision === 'BLOCK';
  
  const audioMatched = challenge.audio_passed === true;
  const audioFailed = challenge.audio_passed === false;
  
  const visualMatched = challenge.visual_presence_passed === true;
  const challengePassed = challenge.challenge_passed === true;
  
  return (
    <div className={`final-decision ${isPass ? 'pass' : 'block'}`} style={{ padding: '24px', textAlign: 'center' }}>
      <h3 style={{ margin: '0 0 16px 0', fontSize: 'var(--text-xl)', color: challengePassed ? 'var(--brand)' : 'var(--alert)' }}>
        {challengePassed ? 'Verification Passed' : 'Verification Failed'}
      </h3>
      
      {!challengePassed && challenge.reason && (
        <p style={{ margin: '0 0 16px 0', color: 'var(--alert)', fontSize: 'var(--text-base)', fontWeight: 'bold' }}>
          {challenge.reason}
        </p>
      )}

      <div style={{ textAlign: 'left', background: 'var(--ink-4)', padding: '16px', borderRadius: '4px', marginBottom: '24px' }}>
        <p style={{ margin: '0 0 8px 0' }}>
          <strong>Audio:</strong><br/>
          {audioMatched ? '✓ Spoken phrase matched' : (audioFailed ? '✗ Spoken phrase mismatch or missing' : '— Not evaluated')}
        </p>
        <p style={{ margin: '0 0 8px 0' }}>
          <strong>Visual:</strong><br/>
          {visualMatched ? '✓ One person detected' : (
            challenge.multiple_faces_detected ? '✗ Multiple people detected' : 
            '✗ No person detected'
          )}
        </p>
        <p style={{ margin: '12px 0 0 0', borderTop: '1px solid var(--ink-3)', paddingTop: '12px' }}>
          <strong>Therefore:</strong><br/>
          {challengePassed ? 'Step-up verification satisfied' : 'Step-up verification NOT satisfied'}
        </p>
      </div>

      {(isPass || isBlock) && (
        <>
          <h3 style={{ margin: '0 0 16px 0', fontSize: 'var(--text-xl)', color: isPass ? 'var(--brand)' : 'var(--ink)' }}>
            {isPass ? 'Action Allowed' : 'Action Blocked'}
          </h3>
          
          <p style={{ margin: '0 0 16px 0', color: 'var(--ink-2)', fontSize: 'var(--text-base)' }}>
            {challenge.final_note}
          </p>
        </>
      )}
      
      {challenge.human_review && (
        <div className="warning-box" style={{ background: 'var(--ink-4)', padding: '12px', borderRadius: '4px', fontSize: 'var(--text-sm)', color: 'var(--ink-2)' }}>
          <strong>Note:</strong> This action has been routed to human review.
        </div>
      )}

      {evidenceList && evidenceList.length > 0 && (
        <div style={{ marginTop: '24px', textAlign: 'left' }}>
          <h4 style={{ marginBottom: '12px' }}>Recording evidence</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {evidenceList.map(ev => (
              <EvidenceCard key={ev.id} evidence={ev} onRemove={null} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
