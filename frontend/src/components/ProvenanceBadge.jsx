import { SOURCE_META } from '../utils/constants';
import '../styles/Provenance.css';

export function ProvenanceBadge({ source }) {
  const meta = SOURCE_META[source];
  if (!meta) return null;
  
  return (
    <span className={`provenance-badge ${source}`} title={meta.hint}>
      {meta.label}
    </span>
  );
}

export function ProvenanceLegend() {
  return (
    <div className="provenance-legend">
      {Object.entries(SOURCE_META).map(([key, meta]) => (
        <div key={key} className="provenance-legend-item">
          <ProvenanceBadge source={key} />
          <span className="provenance-hint">{meta.hint}</span>
        </div>
      ))}
    </div>
  );
}
