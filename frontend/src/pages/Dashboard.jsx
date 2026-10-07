import { useEffect, useState } from 'react';
import { Sheet } from '../components/Sheet';
import { ErrorState } from '../components/ErrorState';
import { getHistory } from '../services/api';
import { Link } from 'react-router-dom';
import '../styles/Dashboard.css';

import { useBackendStatus } from '../hooks/useBackendStatus';

export default function Dashboard() {
  const { epoch } = useBackendStatus();
  const [historyData, setHistoryData] = useState(null);
  const [error, setError] = useState(null);

  const fetchBackendData = async () => {
    try {
      setError(null);
      const hist = await getHistory({ limit: 50 });
      setHistoryData(hist);
    } catch (err) {
      setError(err);
    }
  };

  useEffect(() => {
    fetchBackendData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [epoch]);

  let totalVerifications = 0;
  let blockedCount = 0;
  let verifyCount = 0;
  let allowedCount = 0;
  let recentActivity = [];
  
  if (historyData) {
    totalVerifications = historyData.total || historyData.items.length;
    historyData.items.forEach(item => {
      const dec = item.effective_decision || item.decision;
      if (dec === 'BLOCK') blockedCount++;
      else if (dec === 'VERIFY') verifyCount++;
      else if (dec === 'ALLOW') allowedCount++;
    });
    recentActivity = historyData.items.slice(0, 8);
  }

  const getDecisionColor = (decision) => {
    if (decision === 'ALLOW') return 'var(--allow)';
    if (decision === 'BLOCK') return 'var(--block)';
    if (decision === 'VERIFY') return 'var(--verify)';
    return 'var(--ink-2)';
  };

  return (
    <div className="container dashboard-page" style={{ paddingBottom: 'var(--space-8)' }}>
      <div className="page-header" style={{ marginBottom: 'var(--space-8)' }}>
        <h1 className="hero-title" style={{ fontSize: '64px', lineHeight: '1.1', marginBottom: '24px' }}>
          Real-Time Trust & Risk Overview
        </h1>
        <p className="hero-subtitle" style={{ fontSize: '24px', color: 'var(--ink-2)', maxWidth: '800px', marginBottom: '32px' }}>
          Monitor identity, evidence, decisions, and verification activity from one place.
        </p>
      </div>

      {error ? (
        <ErrorState error={error} onRetry={fetchBackendData} />
      ) : !historyData ? (
        <div style={{ padding: '48px', textAlign: 'center', color: 'var(--ink-3)' }}>Loading Overview...</div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-8)' }}>
            <div style={{ background: 'var(--sheet)', padding: 'var(--space-4)', borderRadius: 'var(--radius)', border: '1px solid var(--rule)' }}>
              <div style={{ fontSize: '48px', fontWeight: 'bold', color: 'var(--ink)', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>{totalVerifications}</div>
              <div style={{ fontSize: 'var(--text-sm)', color: 'var(--ink-2)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Verifications</div>
            </div>
            <div style={{ background: 'var(--sheet)', padding: 'var(--space-4)', borderRadius: 'var(--radius)', border: '1px solid var(--rule)' }}>
              <div style={{ fontSize: '48px', fontWeight: 'bold', color: 'var(--block)', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>{blockedCount}</div>
              <div style={{ fontSize: 'var(--text-sm)', color: 'var(--ink-2)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>High-Risk Actions Blocked</div>
            </div>
            <div style={{ background: 'var(--sheet)', padding: 'var(--space-4)', borderRadius: 'var(--radius)', border: '1px solid var(--rule)' }}>
              <div style={{ fontSize: '48px', fontWeight: 'bold', color: 'var(--verify)', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>{verifyCount}</div>
              <div style={{ fontSize: 'var(--text-sm)', color: 'var(--ink-2)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Actions Requiring Verification</div>
            </div>
            <div style={{ background: 'var(--sheet)', padding: 'var(--space-4)', borderRadius: 'var(--radius)', border: '1px solid var(--rule)' }}>
              <div style={{ fontSize: '48px', fontWeight: 'bold', color: 'var(--allow)', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>{allowedCount}</div>
              <div style={{ fontSize: 'var(--text-sm)', color: 'var(--ink-2)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Low-Risk Actions Allowed</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: 'var(--space-6)', marginBottom: 'var(--space-8)' }}>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
              <Sheet title="Recent Security Activity">
                {recentActivity.length === 0 ? (
                  <div style={{ padding: '24px', textAlign: 'center', color: 'var(--ink-3)' }}>
                    <p style={{ marginBottom: '8px' }}>No recent verification activity.</p>
                    <p>Run an analysis to see security decisions here.</p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {recentActivity.map(item => {
                      const dec = item.effective_decision || item.decision;
                      const color = getDecisionColor(dec);
                      const textColor = dec === 'ALLOW' ? 'var(--allow-text)' : dec === 'BLOCK' ? 'var(--block-text)' : dec === 'VERIFY' ? 'var(--verify-text)' : 'var(--ink)';

                      return (
                        <div key={item.case_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: '1px solid var(--rule)' }}>
                          <div>
                            <div style={{ fontWeight: '600', marginBottom: '4px', color: 'var(--ink)' }}>{item.scenario_title || 'Analysis'}</div>
                            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)', fontFamily: 'var(--font-mono)' }}>
                              {new Date(item.timestamp).toLocaleString()} • Risk: {item.risk_level?.toUpperCase()}
                            </div>
                          </div>
                          <div style={{ padding: '6px 12px', borderRadius: '4px', fontSize: 'var(--text-sm)', fontWeight: 'bold', color: '#fff', background: color, fontFamily: 'var(--font-mono)' }}>
                            {dec}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </Sheet>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
              <Sheet title="Risk Distribution">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  {['LOW', 'MEDIUM', 'HIGH'].map(level => {
                    const count = historyData.items.filter(i => (i.risk_level || '').toUpperCase() === level).length;
                    const percent = historyData.items.length > 0 ? (count / historyData.items.length) * 100 : 0;
                    
                    let color = 'var(--ink-3)';
                    if (level === 'LOW') color = 'var(--allow)';
                    if (level === 'MEDIUM') color = 'var(--verify)';
                    if (level === 'HIGH') color = 'var(--block)';

                    return (
                      <div key={level}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: 'var(--text-sm)', fontFamily: 'var(--font-mono)' }}>
                          <span style={{ fontWeight: 'bold', color: 'var(--ink)' }}>{level} RISK</span>
                          <span style={{ color: 'var(--ink-2)' }}>{count} ({Math.round(percent)}%)</span>
                        </div>
                        <div style={{ height: '8px', background: 'var(--rule)', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${percent}%`, background: color }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Sheet>

              <Sheet title="Quick Actions">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <Link to="/analyze" className="btn btn-primary" style={{ textDecoration: 'none', textAlign: 'center', display: 'block', padding: '12px', borderRadius: 'var(--radius)', background: 'var(--brand)', color: '#fff', fontWeight: '600' }}>
                    Run New Analysis
                  </Link>
                  <Link to="/history" className="btn" style={{ textDecoration: 'none', textAlign: 'center', display: 'block', padding: '12px', borderRadius: 'var(--radius)', background: 'var(--paper-2)', color: 'var(--ink)', border: '1px solid var(--rule)', fontWeight: '600' }}>
                    View History
                  </Link>
                  <Link to="/how" className="btn" style={{ textDecoration: 'none', textAlign: 'center', display: 'block', padding: '12px', borderRadius: 'var(--radius)', background: 'var(--paper-2)', color: 'var(--ink)', border: '1px solid var(--rule)', fontWeight: '600' }}>
                    How TRUSTLOCK Works
                  </Link>
                </div>
              </Sheet>
            </div>
            
          </div>
        </>
      )}
    </div>
  );
}
