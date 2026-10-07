import { DECISION_META } from '../utils/constants';
import '../styles/Stamp.css';

export function Stamp({ decision, caption, animate = true, customLabel }) {
  const meta = DECISION_META[decision];
  const color = meta ? meta.color : 'var(--ink)';
  const label = customLabel || (meta ? meta.label : decision);

  return (
    <div 
      className={`stamp-container ${animate ? 'animate' : ''}`}
      style={{ color }}
      aria-label={`Decision: ${label}`}
    >
      {caption && <div className="stamp-caption">{caption}</div>}
      <div className="stamp" style={{ borderColor: color }}>
        {label}
      </div>
    </div>
  );
}
