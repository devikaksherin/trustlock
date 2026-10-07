import React, { useState, useEffect } from 'react';
import { Sheet } from '../components/Sheet';
import ScenarioCard from '../components/ScenarioCard';
import CaseForm from '../components/CaseForm';
import EvidenceDropzone from '../components/EvidenceDropzone';
import EvidenceCard from '../components/EvidenceCard';
import { getScenarios, analyzeAction, fetchProfiles } from '../services/api';
import { createEmptyCase, loadScenario, updateField, addEvidenceId, removeEvidenceId } from '../utils/caseModel';
import { useEvidence } from '../hooks/useEvidence';
import ResultSheet from '../components/ResultSheet';
import ChallengeModal from '../components/ChallengeModal';
import { ErrorState } from '../components/ErrorState';

import { useBackendStatus } from '../hooks/useBackendStatus';

export default function Analyze() {
  const { epoch } = useBackendStatus();
  const [scenarios, setScenarios] = useState([]);
  const [caseState, setCaseState] = useState(createEmptyCase());
  const { evidenceList, isUploading, uploadProgress, uploadError, addFiles, removeEvidence } = useEvidence();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState(null);
  const [result, setResult] = useState(null);
  const [challengeId, setChallengeId] = useState(null);

  const [scenariosError, setScenariosError] = useState(null);
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(true);

  const [profiles, setProfiles] = useState([]);
  const [profilesError, setProfilesError] = useState(null);

  useEffect(() => {
    setIsLoadingScenarios(true);
    getScenarios()
      .then(data => {
        setScenarios(data);
        setScenariosError(null);
      })
      .catch(err => setScenariosError(err))
      .finally(() => setIsLoadingScenarios(false));
      
    fetchProfiles()
      .then(data => {
        setProfiles(data);
        setProfilesError(null);
      })
      .catch(err => setProfilesError(err));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [epoch]);

  useEffect(() => {
    if (result && result.challenge_id) {
      setChallengeId(result.challenge_id);
    }
  }, [result]);

  const handleSelectScenario = (scenario) => {
    setCaseState(loadScenario(scenario));
  };

  const handleUpdateField = (section, field, value) => {
    setCaseState(prev => updateField(prev, section, field, value));
  };

  const handleFilesSelected = async (files) => {
    const uploaded = await addFiles(files);
    if (uploaded) {
      setCaseState(prev => {
        let next = prev;
        uploaded.forEach(ev => {
          next = addEvidenceId(next, ev.id);
        });
        return next;
      });
    }
  };
  
  const handleRemoveEvidence = (id) => {
    removeEvidence(id);
    setCaseState(prev => removeEvidenceId(prev, id));
  };

  const handleSubmit = async () => {
    setIsAnalyzing(true);
    setChallengeId(null);
    try {
      const res = await analyzeAction(caseState);
      setResult(res);
      setAnalyzeError(null);
    } catch (err) {
      console.error(err);
      setAnalyzeError(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (result) {
    return (
      <div className="container" style={{ paddingBottom: 'var(--space-8)' }}>
        <div className="page-header">
          <div className="eyebrow">02 · ANALYZE</div>
          <h1 style={{ fontSize: '40px', marginTop: 'var(--space-3)' }}>Analysis Complete</h1>
        </div>
        
        <ResultSheet 
          result={result} 
          onRestart={() => setResult(null)} 
          onIssueChallenge={(id) => setChallengeId(id)} 
        />
        
        {challengeId && (
          <ChallengeModal 
            challengeId={challengeId} 
            onClose={() => setChallengeId(null)}
          />
        )}
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingBottom: 'var(--space-8)' }}>
      <div className="page-header">
        <div className="eyebrow">02 · ANALYZE</div>
        <h1 style={{ fontSize: '40px', marginTop: 'var(--space-3)' }}>Run Analysis</h1>
        <p style={{ color: 'var(--ink-2)', fontSize: '20px', marginTop: 'var(--space-2)' }}>Select a scenario or enter manual data.</p>
      </div>

      <div style={{ marginBottom: 'var(--space-6)' }}>
        <h2 style={{ marginBottom: 'var(--space-4)', fontSize: '24px' }}>Scenarios</h2>
        {isLoadingScenarios ? (
          <p>Loading scenarios...</p>
        ) : scenariosError ? (
          <ErrorState error={scenariosError} onRetry={() => {
            setIsLoadingScenarios(true);
            getScenarios().then(data => { setScenarios(data); setScenariosError(null); }).catch(setScenariosError).finally(() => setIsLoadingScenarios(false));
          }} />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 'var(--space-4)' }}>
            {scenarios.map(s => (
              <ScenarioCard key={s.id} scenario={s} onSelect={handleSelectScenario} />
            ))}
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: 'var(--space-6)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          <Sheet title="Case Configuration">
            <div style={{ marginBottom: 'var(--space-4)', paddingBottom: 'var(--space-4)', borderBottom: '1px solid var(--border)' }}>
              <label style={{ display: 'block', fontSize: '14px', color: 'var(--ink-2)', marginBottom: '8px', fontWeight: '500' }}>Select Trust Profile</label>
              <select 
                style={{ width: '100%', padding: '8px 12px', background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--ink)', borderRadius: '4px' }}
                value={caseState.profile_id || ""}
                onChange={e => setCaseState(prev => ({...prev, profile_id: e.target.value || null}))}
              >
                <option value="">No Profile (Skip Context Checks)</option>
                {profiles.map(p => (
                  <option key={p.id} value={p.id}>{p.display_name} {p.demo ? '(Demo)' : ''}</option>
                ))}
              </select>
            </div>
            <CaseForm caseState={caseState} onUpdate={handleUpdateField} />
          </Sheet>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          <Sheet title="Evidence Locker">
            <EvidenceDropzone 
              onFilesSelected={handleFilesSelected} 
              isUploading={isUploading} 
              progress={uploadProgress} 
            />
            {uploadError && <p style={{ color: 'var(--block-text)', marginTop: '8px' }}>{uploadError}</p>}
            
            {evidenceList.length > 0 && (
              <div style={{ marginTop: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {evidenceList.map(ev => (
                  <EvidenceCard key={ev.id} evidence={ev} onRemove={handleRemoveEvidence} />
                ))}
              </div>
            )}
          </Sheet>
          
          
          {analyzeError && (
            <ErrorState error={analyzeError} onRetry={handleSubmit} />
          )}

          <button 
            className="btn btn-primary" 
            style={{ padding: '16px', fontSize: '18px', width: '100%', justifyContent: 'center' }}
            onClick={handleSubmit}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? "Analyzing..." : "Analyze Case"}
          </button>
        </div>
      </div>
    </div>
  );
}
