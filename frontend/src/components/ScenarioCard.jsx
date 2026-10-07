import React from 'react';
import '../styles/ScenarioCard.css';

export default function ScenarioCard({ scenario, onSelect }) {
  if (!scenario) return null;
  return (
    <div className="scenario-card" onClick={() => onSelect(scenario)}>
      <div className="scenario-header">
        <h3 className="scenario-title">{scenario.title}</h3>
        {scenario.featured && <span className="featured-badge">Featured</span>}
      </div>
      <p className="scenario-narrative">{scenario.narrative}</p>
    </div>
  );
}
