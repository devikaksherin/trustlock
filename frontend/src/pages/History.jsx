import React, { useState, useEffect } from 'react';
import { Sheet } from '../components/Sheet';
import { ErrorState } from '../components/ErrorState';
import { getHistory, resetHistory, verifyLedger, getCase } from '../services/api';

import { useBackendStatus } from '../hooks/useBackendStatus';

export default function History() {
  const { epoch } = useBackendStatus();
  const [history, setHistory] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [expandedRows, setExpandedRows] = useState({});
  const [caseDetails, setCaseDetails] = useState({});
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [historyError, setHistoryError] = useState(null);

  const fetchHistory = async () => {
    setLoading(true);
    setHistoryError(null);
    try {
      const res = await getHistory({ decision: filter });
      setHistory(res.items || []);
    } catch (e) {
      console.error(e);
      setHistoryError(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  useEffect(() => {
    fetchHistory();
    if (verificationResult) handleVerify();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [epoch]);

  const toggleRow = async (caseId) => {
    setExpandedRows(prev => ({ ...prev, [caseId]: !prev[caseId] }));
    
    if (!caseDetails[caseId]) {
      try {
        const details = await getCase(caseId);
        setCaseDetails(prev => ({ ...prev, [caseId]: details }));
      } catch (e) {
        console.error("Failed to load case", e);
      }
    }
  };

  const handleVerify = async () => {
    setVerifying(true);
    setVerificationResult(null);
    try {
      const res = await verifyLedger();
      setVerificationResult(res);
    } catch (e) {
      setVerificationResult({ valid: false, error: e.message });
    } finally {
      setVerifying(false);
    }
  };

  const handleReset = async () => {
    if (confirm("Are you sure you want to delete all history?")) {
      try {
        await resetHistory();
        fetchHistory();
        setExpandedRows({});
        setCaseDetails({});
        setVerificationResult(null);
      } catch (e) {
        alert("Failed to reset history: " + e.message);
      }
    }
  };

  return (
    <div className="container" style={{ paddingBottom: 'var(--space-8)' }}>
      <div className="page-header">
        <div className="eyebrow">03 · HISTORY</div>
        <h1 style={{ fontSize: '40px', marginTop: 'var(--space-3)' }}>Ledger History</h1>
        <p style={{ color: 'var(--ink-2)', fontSize: '20px', marginTop: 'var(--space-2)' }}>Immutable record of past analyses and decisions.</p>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('all')}>All</button>
          <button className={`btn ${filter === 'allow' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('allow')}>Allowed</button>
          <button className={`btn ${filter === 'block' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('block')}>Blocked</button>
          <button className={`btn ${filter === 'verify' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('verify')}>Verified</button>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary" onClick={handleVerify} disabled={verifying}>
            {verifying ? 'Verifying...' : 'Verify Ledger'}
          </button>
          <button className="btn btn-secondary" onClick={handleReset} style={{ color: 'var(--block-text)', borderColor: 'var(--block)' }}>Reset</button>
        </div>
      </div>

      {verificationResult && (
        <div style={{ padding: '16px', background: verificationResult.valid ? 'var(--allow)' : 'var(--block)', color: 'var(--paper)', marginBottom: '16px', borderRadius: '4px' }}>
          {verificationResult.valid ? `Ledger verified. Length: ${verificationResult.length}. Time: ${verificationResult.time_ms}ms` : `Verification failed: ${verificationResult.error}`}
        </div>
      )}

      <Sheet>
        {loading ? (
          <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div>
        ) : historyError ? (
          <ErrorState error={historyError} onRetry={fetchHistory} />
        ) : history.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--ink-2)' }}>No history found.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--ink-4)', textAlign: 'left', color: 'var(--ink-2)', fontSize: 'var(--text-sm)' }}>
                <th style={{ padding: '12px 16px' }}>Timestamp</th>
                <th style={{ padding: '12px 16px' }}>Case ID</th>
                <th style={{ padding: '12px 16px' }}>Decision</th>
                <th style={{ padding: '12px 16px' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {history.map(row => (
                <React.Fragment key={row.case_id}>
                  <tr 
                    style={{ borderBottom: '1px solid var(--ink-4)', cursor: 'pointer' }} 
                    onClick={() => toggleRow(row.case_id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        toggleRow(row.case_id);
                      }
                    }}
                    tabIndex={0}
                    role="button"
                    aria-expanded={!!expandedRows[row.case_id]}
                  >
                    <td style={{ padding: '12px 16px', color: 'var(--ink-2)', fontSize: 'var(--text-sm)' }}>
                      {new Date(row.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
                      {row.case_id.substring(0, 8)}...
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ 
                        padding: '4px 8px', 
                        borderRadius: '2px', 
                        fontSize: 'var(--text-xs)', 
                        fontWeight: '600',
                        background: `var(--${row.decision.toLowerCase()})`,
                        color: 'var(--paper)'
                      }}>
                        {row.decision}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <button className="btn" style={{ padding: '4px 8px', fontSize: 'var(--text-xs)' }}>
                        {expandedRows[row.case_id] ? 'Collapse' : 'Expand'}
                      </button>
                    </td>
                  </tr>
                  {expandedRows[row.case_id] && (
                    <tr style={{ background: 'var(--surface)' }}>
                      <td colSpan="4" style={{ padding: '16px' }}>
                        {caseDetails[row.case_id] ? (
                          <pre style={{ margin: 0, fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', overflowX: 'auto' }}>
                            {JSON.stringify(caseDetails[row.case_id], null, 2)}
                          </pre>
                        ) : (
                          <div>Loading details...</div>
                        )}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        )}
      </Sheet>
    </div>
  );
}
