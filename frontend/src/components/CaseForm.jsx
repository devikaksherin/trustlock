import React from 'react';
import '../styles/CaseForm.css';

export default function CaseForm({ caseState, onUpdate }) {
  const handleChange = (section, field, value) => {
    onUpdate(section, field, value);
  };
  
  return (
    <div className="case-form">
      {['identity', 'context', 'behavior', 'transaction'].map(section => {
        if (!caseState[section]) return null;
        return (
          <div key={section} className="form-section">
            <h4 className="section-title">{section.charAt(0).toUpperCase() + section.slice(1)}</h4>
            <div className="form-grid">
              {Object.keys(caseState[section]).map(field => {
                if (field === 'sources') return null;
                const val = caseState[section][field];
                const type = typeof val;
                
                if (type === 'boolean') {
                  return (
                    <label key={field} className="form-field checkbox">
                      <input 
                        type="checkbox" 
                        checked={val}
                        onChange={e => handleChange(section, field, e.target.checked)}
                      />
                      <span className="field-label">{field.replace(/_/g, ' ')}</span>
                    </label>
                  );
                }
                
                if (type === 'number') {
                  return (
                    <label key={field} className="form-field">
                      <span className="field-label">{field.replace(/_/g, ' ')}</span>
                      <input 
                        type="number" 
                        value={val}
                        onChange={e => handleChange(section, field, parseFloat(e.target.value) || 0)}
                      />
                    </label>
                  );
                }
                
                return (
                  <label key={field} className="form-field">
                    <span className="field-label">{field.replace(/_/g, ' ')}</span>
                    <input 
                      type="text" 
                      value={val || ""}
                      onChange={e => handleChange(section, field, e.target.value)}
                    />
                  </label>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
