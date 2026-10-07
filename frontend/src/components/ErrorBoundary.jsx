import React from 'react';
import { Sheet } from './Sheet';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="container" style={{ padding: '48px 0', textAlign: 'center' }}>
          <Sheet title="Something went wrong">
            <p style={{ marginBottom: '24px' }}>We encountered an unexpected error.</p>
            <button className="btn btn-primary" onClick={() => window.location.reload()}>
              Reload Page
            </button>
          </Sheet>
        </div>
      );
    }
    return this.props.children;
  }
}
