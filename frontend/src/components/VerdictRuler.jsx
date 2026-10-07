export default function VerdictRuler({ trustScore }) {
  const pointerLeft = `${Math.max(0, Math.min(100, trustScore))}%`;
  
  return (
    <div className="verdict-ruler" style={{ marginTop: '32px', marginBottom: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: 'var(--text-sm)', color: 'var(--ink-2)' }}>
        <span>BLOCK (0-39)</span>
        <span>VERIFY (40-79)</span>
        <span>ALLOW (80-100)</span>
      </div>
      
      <div style={{ position: 'relative', height: '12px', borderRadius: '6px', background: 'linear-gradient(to right, var(--block) 0%, var(--block) 39.9%, var(--verify) 40%, var(--verify) 79.9%, var(--allow) 80%, var(--allow) 100%)' }}>
        <div style={{
          position: 'absolute',
          left: pointerLeft,
          top: '-6px',
          width: '4px',
          height: '24px',
          background: 'var(--ink)',
          transform: 'translateX(-50%)',
          borderRadius: '2px',
          boxShadow: '0 0 0 2px var(--paper)'
        }} />
      </div>
      <div style={{ textAlign: 'center', marginTop: '16px', fontSize: 'var(--text-xl)', fontWeight: '600' }}>
        Trust Score: {trustScore}
      </div>
    </div>
  );
}
