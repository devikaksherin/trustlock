import React, { useState, useEffect } from 'react';
import { Sheet } from '../components/Sheet';
import Stepper from '../components/Stepper';
import { ErrorState } from '../components/ErrorState';
import { getConfig } from '../services/api';

export default function HowItWorks() {
  const [config, setConfig] = useState(null);
  const [configError, setConfigError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getConfig()
      .then(data => { setConfig(data); setConfigError(null); })
      .catch(setConfigError)
      .finally(() => setLoading(false));
  }, []);

  const steps = [
    { label: 'Ingest Evidence' },
    { label: 'Multimodal Analysis' },
    { label: 'Risk Calculation' },
    { label: 'Decision Engine' },
    { label: 'Dynamic Challenge' }
  ];

  return (
    <div className="container" style={{ paddingBottom: 'var(--space-8)' }}>
      <div className="page-header">
        <div className="eyebrow">04 · HOW IT WORKS</div>
        <h1 style={{ fontSize: '40px', marginTop: 'var(--space-3)' }}>The Methodology</h1>
        <p style={{ color: 'var(--ink-2)', fontSize: '20px', marginTop: 'var(--space-2)' }}>Understanding the multimodal analysis framework.</p>
      </div>

      <Sheet title="Pipeline Architecture">
        <p style={{ marginBottom: '24px' }}>
          TrustLock operates a deterministic pipeline that evaluates context, intent, and evidence simultaneously.
        </p>
        <Stepper steps={steps} activeIndex={-1} staticMode={true} />
      </Sheet>

      <div style={{ marginTop: '32px' }}>
        <Sheet title="Configuration & Weights">
          <p style={{ marginBottom: '24px' }}>
            The risk engine computes a final Trust Score (0-100) based on weighted subscores from various analyzers.
          </p>
          
          {loading ? (
            <div>Loading configuration...</div>
          ) : configError ? (
            <ErrorState error={configError} onRetry={() => {
              setLoading(true);
              getConfig().then(data => { setConfig(data); setConfigError(null); }).catch(setConfigError).finally(() => setLoading(false));
            }} />
          ) : config ? (
            <div>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '24px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--ink-4)', textAlign: 'left', color: 'var(--ink-2)' }}>
                    <th style={{ padding: '12px 0' }}>Analyzer Category</th>
                    <th style={{ padding: '12px 0', textAlign: 'right' }}>Weight</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(config.weights).map(([key, val]) => (
                    <tr key={key} style={{ borderBottom: '1px solid var(--ink-4)' }}>
                      <td style={{ padding: '12px 0', textTransform: 'capitalize' }}>{key}</td>
                      <td style={{ padding: '12px 0', textAlign: 'right' }}>{(val * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--ink-4)', textAlign: 'left', color: 'var(--ink-2)' }}>
                    <th style={{ padding: '12px 0' }}>Threshold</th>
                    <th style={{ padding: '12px 0', textAlign: 'right' }}>Score Range</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: '1px solid var(--ink-4)' }}>
                    <td style={{ padding: '12px 0', fontWeight: '600', color: 'var(--block-text)' }}>BLOCK</td>
                    <td style={{ padding: '12px 0', textAlign: 'right' }}>0 - {config.thresholds.block - 1}</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid var(--ink-4)' }}>
                    <td style={{ padding: '12px 0', fontWeight: '600', color: 'var(--verify-text)' }}>VERIFY</td>
                    <td style={{ padding: '12px 0', textAlign: 'right' }}>{config.thresholds.block} - {config.thresholds.verify - 1}</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid var(--ink-4)' }}>
                    <td style={{ padding: '12px 0', fontWeight: '600', color: 'var(--allow-text)' }}>ALLOW</td>
                    <td style={{ padding: '12px 0', textAlign: 'right' }}>{config.thresholds.verify} - 100</td>
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <div>Loading configuration...</div>
          )}
        </Sheet>
      </div>

      <div style={{ marginTop: '32px', padding: '16px', background: 'var(--ink-4)', borderRadius: '4px', fontSize: 'var(--text-sm)', color: 'var(--ink-2)' }}>
        <strong>Disclaimer:</strong> This is a demonstration environment. All evidence uploaded is ephemeral and processed locally or via mock APIs. No real identity data is stored.
      </div>
    </div>
  );
}
