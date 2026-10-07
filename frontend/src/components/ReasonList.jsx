export default function ReasonList({ reasons }) {
  if (!reasons || reasons.length === 0) return null;
  
  return (
    <div className="reason-list" style={{ marginTop: '32px' }}>
      <h3 style={{ fontSize: 'var(--text-lg)', marginBottom: '16px' }}>Key Findings</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {reasons.map((r, i) => (
          <div key={i} className={`reason-card severity-${r.severity}`} style={{ 
            padding: '16px', 
            borderRadius: '4px',
            borderLeft: `4px solid var(--${r.severity === 'high' ? 'block' : r.severity === 'medium' ? 'verify' : r.severity === 'low' ? 'ink-2' : 'allow'})`,
            background: 'var(--surface)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{ fontWeight: '600', textTransform: 'uppercase', fontSize: 'var(--text-xs)', color: 'var(--ink-2)' }}>{r.category}</span>
                {r.source === 'profile' && <span className="provenance-badge profile">PROFILE</span>}
              </div>
              <span style={{ textTransform: 'uppercase', fontSize: 'var(--text-xs)', fontWeight: '600', color: `var(--${r.severity === 'high' ? 'block' : r.severity === 'medium' ? 'verify' : r.severity === 'low' ? 'ink-2' : 'allow'})` }}>
                {r.severity}
              </span>
            </div>
            <div style={{ fontWeight: '600', marginBottom: '4px' }}>{r.title}</div>
            <div style={{ fontSize: 'var(--text-sm)', color: 'var(--ink-2)' }}>{r.description}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
