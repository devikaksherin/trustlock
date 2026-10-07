export default function RiskBreakdown({ breakdown, convergenceBonus }) {
  if (!breakdown) return null;
  return (
    <div className="risk-breakdown" style={{ marginTop: '32px' }}>
      <h3 style={{ fontSize: 'var(--text-lg)', marginBottom: '16px' }}>Risk Breakdown</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--ink-4)', textAlign: 'left', color: 'var(--ink-2)', fontSize: 'var(--text-sm)' }}>
            <th style={{ padding: '8px 0' }}>Category</th>
            <th style={{ padding: '8px 0', textAlign: 'right' }}>Weight</th>
            <th style={{ padding: '8px 0', textAlign: 'right' }}>Risk Subscore</th>
            <th style={{ padding: '8px 0', textAlign: 'right' }}>Contribution</th>
          </tr>
        </thead>
        <tbody>
          {breakdown.map(b => (
            <tr key={b.category} style={{ borderBottom: '1px solid var(--ink-4)' }}>
              <td style={{ padding: '12px 0', textTransform: 'capitalize' }}>{b.category}</td>
              <td style={{ padding: '12px 0', textAlign: 'right' }}>{(b.weight * 100).toFixed(0)}%</td>
              <td style={{ padding: '12px 0', textAlign: 'right' }}>{b.sub_risk}</td>
              <td style={{ padding: '12px 0', textAlign: 'right' }}>{b.contribution.toFixed(1)}</td>
            </tr>
          ))}
          {convergenceBonus > 0 && (
            <tr style={{ borderBottom: '1px solid var(--ink-4)' }}>
              <td style={{ padding: '12px 0' }}>Convergence Penalty</td>
              <td style={{ padding: '12px 0', textAlign: 'right' }}>-</td>
              <td style={{ padding: '12px 0', textAlign: 'right' }}>-</td>
              <td style={{ padding: '12px 0', textAlign: 'right', color: 'var(--block-text)' }}>+{convergenceBonus.toFixed(1)}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
