import { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import * as LucideIcons from 'lucide-react';
import { Wordmark } from './Wordmark';
import { StatusPill } from './StatusPill';
import { useBackendStatus } from '../hooks/useBackendStatus';
import { NAV_ITEMS } from '../utils/constants';
import { API_URL } from '../services/api';
import '../styles/Header.css';

export function Header() {
  const { state, reason, lastChecked, retry } = useBackendStatus();
  const [isRetrying, setIsRetrying] = useState(false);

  let bannerText = "";
  if (state === 'offline' || state === 'degraded') {
    if (reason === 'unreachable') bannerText = `Backend unreachable at ${API_URL}.`;
    else if (reason === 'wrong_service') bannerText = `Something else is answering at ${API_URL}, not TRUSTLOCK. Check the port.`;
    else if (reason === 'http_error') bannerText = `The backend returned an error at ${API_URL}.`;
    else if (state === 'degraded') bannerText = "Backend is reachable but its storage is unavailable. Analysis may fail.";
    else bannerText = "Backend is offline.";
  }

  const timeStr = lastChecked ? lastChecked.toLocaleTimeString('en-US', { hour12: false }) : "";

  const handleRetry = async () => {
    setIsRetrying(true);
    await retry();
    setIsRetrying(false);
  };

  return (
    <>
      <header className="header">
        <div className="container header-container">
          <Link to="/" className="header-logo" aria-label="Home">
            <Wordmark size={24} />
          </Link>
          
          <nav className="header-nav">
            {NAV_ITEMS.map(item => (
              <NavLink 
                key={item.to} 
                to={item.to} 
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                end={item.to === "/"}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          
          <div className="header-status">
            <StatusPill status={state} />
          </div>
        </div>
      </header>
      
      {(state === 'offline' || state === 'degraded') && (
        <div className="offline-banner">
          <div className="container banner-container">
            <div>
              <p>{bannerText} Last checked {timeStr}</p>
              <div className="banner-cmd mono">.\backend\run.ps1</div>
            </div>
            <button className="btn btn-secondary banner-btn" onClick={handleRetry} disabled={isRetrying}>
              {isRetrying ? 'Checking…' : 'Retry'}
            </button>
          </div>
        </div>
      )}

      <nav className="bottom-tabbar">
        {NAV_ITEMS.map(item => {
          const Icon = LucideIcons[item.icon];
          return (
            <NavLink 
              key={item.to} 
              to={item.to} 
              className={({ isActive }) => `tab-link ${isActive ? 'active' : ''}`}
              end={item.to === "/"}
            >
              <Icon size={20} />
              <span className="tab-label">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </>
  );
}
