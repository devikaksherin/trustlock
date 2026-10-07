import { Link } from 'react-router-dom';
import { EmptyState } from '../components/EmptyState';
import { SearchX } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="container" style={{ paddingTop: 'var(--space-8)', paddingBottom: 'var(--space-8)' }}>
      <EmptyState
        icon={SearchX}
        title="Page Not Found"
        message="The page you are looking for doesn't exist or has been moved."
        action={
          <Link to="/" className="btn btn-primary">
            Back to Dashboard
          </Link>
        }
      />
    </div>
  );
}
