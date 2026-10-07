import { useEffect } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { ErrorBoundary } from './components/ErrorBoundary';

import Dashboard from './pages/Dashboard';
import Analyze from './pages/Analyze';
import TrustProfile from './pages/TrustProfile';
import History from './pages/History';
import HowItWorks from './pages/HowItWorks';
import NotFound from './pages/NotFound';

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <a href="#main" className="sr-only" style={{ top: 0, left: 0, zIndex: 9999, background: 'var(--paper)', padding: 'var(--space-2)', color: 'var(--ink)' }}>Skip to content</a>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Header />
        <main id="main" tabIndex={-1} style={{ flex: 1, outline: 'none' }}>
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/analyze" element={<Analyze />} />
                <Route path="/profile" element={<TrustProfile />} />
                <Route path="/history" element={<History />} />
                <Route path="/how-it-works" element={<HowItWorks />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </ErrorBoundary>
        </main>
        <Footer />
      </div>
    </>
  );
}
