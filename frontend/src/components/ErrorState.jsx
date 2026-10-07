import { friendlyMessage } from '../services/api';
import '../styles/ErrorState.css';

export function ErrorState({ error, onRetry }) {
  let title = "An error occurred";
  
  if (error && error.kind) {
    if (error.kind === "network") title = "Can't reach the backend";
    else if (error.kind === "validation") title = "The request was rejected";
    else if (error.kind === "server") title = "The backend hit an error";
  } else if (typeof error === 'string') {
    title = "Error";
  }

  const message = friendlyMessage(error);

  return (
    <div className="error-state" role="alert">
      <h3 className="error-title">{title}</h3>
      <p className="error-message">{message}</p>
      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
