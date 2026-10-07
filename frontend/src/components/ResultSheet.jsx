import { Sheet } from './Sheet';
import Stepper from './Stepper';
import VerdictRuler from './VerdictRuler';
import RiskBreakdown from './RiskBreakdown';
import ReasonList from './ReasonList';

export default function ResultSheet({ result, onRestart, onIssueChallenge }) {
  if (!result) return null;
  
  const isBlock = result.decision === 'BLOCK';
  const isVerify = result.decision === 'VERIFY';
  
  return (
    <Sheet title="Analysis Result">
      <div className="result-sheet">
        
        <div style={{ padding: '24px', background: `var(--${result.decision.toLowerCase()})`, color: 'var(--paper)', borderRadius: '4px', marginBottom: '24px' }}>
          <h2 style={{ margin: '0 0 8px 0', fontSize: '32px' }}>{result.decision}</h2>
          <p style={{ margin: 0, opacity: 0.9 }}>{result.summary}</p>
        </div>
        
        <VerdictRuler trustScore={result.trust_score} />
        
        <ReasonList reasons={result.reasons} />
        
        <RiskBreakdown breakdown={result.breakdown} convergenceBonus={result.convergence_bonus || 0} />
        
        <div style={{ marginTop: '32px', display: 'flex', gap: '16px' }}>
          {result.challenge_id && (isVerify || isBlock) && (
            <button className="btn-primary" onClick={() => onIssueChallenge(result.challenge_id)}>
              Issue Challenge
            </button>
          )}
          <button className="btn-secondary" onClick={onRestart}>Start Over</button>
        </div>
      </div>
    </Sheet>
  );
}
