import '../styles/StatusPill.css';

export function StatusPill({ status }) {
  const isOnline = status === 'online';
  const isOffline = status === 'offline';
  const isDegraded = status === 'degraded';
  
  let label = "SYSTEM ONLINE";
  let shortLabel = "ONLINE";
  if (isOffline) {
    label = "BACKEND OFFLINE";
    shortLabel = "OFFLINE";
  } else if (isDegraded) {
    label = "BACKEND DEGRADED";
    shortLabel = "DEGRADED";
  } else if (status === 'checking') {
    label = "CHECKING";
    shortLabel = "CHECKING";
  }

  return (
    <div className={`status-pill ${status}`} role="status" aria-live="polite">
      <span className="dot">●</span>
      <span className="full-label">{label}</span>
      <span className="short-label">{shortLabel}</span>
    </div>
  );
}
