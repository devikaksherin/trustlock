import React from 'react';
import { File, Trash2, Video, Mic } from 'lucide-react';
import '../styles/EvidenceCard.css';
import { evidenceFileUrl } from '../services/api';

export default function EvidenceCard({ evidence, onRemove }) {
  if (!evidence) return null;
  
  const sizeKb = Math.round((evidence.sizeBytes || 0) / 1024);
  const isVideo = evidence.mime?.startsWith('video/');
  const isAudio = evidence.mime?.startsWith('audio/');
  const url = evidenceFileUrl(evidence.id);
  
  const getFinding = (key) => evidence.findings?.find(f => f.key === key)?.value;
  const duration = getFinding('duration');
  const sampleRate = getFinding('sample_rate');
  
  return (
    <div className="evidence-card" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div className="evidence-icon">
          {isVideo ? <Video size={24} /> : isAudio ? <Mic size={24} /> : <File size={24} />}
        </div>
        <div className="evidence-details" style={{ flex: 1 }}>
          <div className="evidence-header">
            <span className="evidence-name">{evidence.originalName}</span>
            <span className="evidence-size">{sizeKb} KB</span>
          </div>
          <div className="evidence-meta">
            <span className="meta-item">{evidence.mime}</span>
            {evidence.sha256 && (
              <span className="meta-item hash">{evidence.sha256.substring(0, 8)}...</span>
            )}
          </div>
        </div>
        {onRemove && (
          <button 
            className="btn-remove btn-ghost" 
            onClick={(e) => { e.stopPropagation(); onRemove(evidence.id); }}
            aria-label="Remove evidence"
          >
            <Trash2 size={16} />
          </button>
        )}
      </div>

      {(isVideo || isAudio) && (
        <div style={{ marginTop: '8px' }}>
          {isVideo ? (
            <video 
              src={url} 
              controls 
              preload="metadata" 
              style={{ width: '100%', maxHeight: '200px', background: '#000', borderRadius: '4px' }} 
              onError={(e) => e.target.outerHTML = "<div style='color:red;font-size:0.85rem'>This browser cannot play this video format. The file is stored and analysed.</div>"}
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <audio 
                src={url} 
                controls 
                preload="metadata" 
                style={{ width: '100%' }}
                onError={(e) => {
                  const div = document.createElement('div');
                  div.style.color = 'red';
                  div.style.fontSize = '0.85rem';
                  div.textContent = "This browser cannot play this audio format. The file is stored and analysed.";
                  e.target.parentNode.replaceChild(div, e.target);
                }}
              />
              <div style={{ fontSize: '0.75rem', color: 'var(--ink-2)' }}>
                {duration && <span>Duration: {duration}s </span>}
                {sampleRate && <span>| Sample Rate: {sampleRate}Hz</span>}
              </div>
            </div>
          )}
        </div>
      )}

      {evidence.findings && evidence.findings.length > 0 && (
        <div style={{ fontSize: '0.8rem', background: 'var(--ink-4)', padding: '6px', borderRadius: '4px' }}>
          <strong>Findings: </strong>
          {evidence.findings.map(f => (
            <span key={f.key} style={{ marginRight: '8px' }}>{f.label}: {typeof f.value === 'number' ? f.value.toFixed(2) : f.value}</span>
          ))}
        </div>
      )}
    </div>
  );
}
