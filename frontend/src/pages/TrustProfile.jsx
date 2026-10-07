import React, { useState, useEffect } from 'react';
import { Sheet } from '../components/Sheet';
import { ErrorState } from '../components/ErrorState';
import { fetchProfiles, saveProfile, deleteProfile } from '../services/api';
import { UserCheck, Plus, Trash2, Edit2, Save, X } from 'lucide-react';
import '../styles/TrustProfile.css';

const ListInput = ({ value, onChange, placeholder, style }) => {
  const [localVal, setLocalVal] = useState((value || []).join(', '));
  
  useEffect(() => {
    setLocalVal((value || []).join(', '));
  }, [value]);

  const handleBlur = () => {
    const arr = localVal.split(',').map(s => s.trim()).filter(Boolean);
    onChange(arr);
  };

  return (
    <input 
      type="text" 
      placeholder={placeholder} 
      value={localVal} 
      onChange={e => setLocalVal(e.target.value)} 
      onBlur={handleBlur}
      style={style}
    />
  );
};

export default function TrustProfile() {
  const [profiles, setProfiles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [editingProfile, setEditingProfile] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const loadProfiles = async () => {
    setIsLoading(true);
    try {
      const data = await fetchProfiles();
      setProfiles(data);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProfiles();
  }, []);

  const handleCreateNew = () => {
    const newProfile = {
      id: `usr_${Date.now()}`,
      display_name: "New Profile",
      user_id: "",
      role: "User",
      organisation: "",
      baseline: {
        usual_devices: [],
        usual_locations: [],
        normal_hours: { start: 9, end: 18 },
        usual_channels: [],
        trusted_contacts: [],
        trusted_issuers: [],
        transaction_patterns: []
      },
      notes: "",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      demo: false
    };
    setEditingProfile(newProfile);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const p = { ...editingProfile, updated_at: new Date().toISOString() };
      await saveProfile(p);
      setEditingProfile(null);
      await loadProfiles();
    } catch (err) {
      alert("Error saving profile: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this profile?")) return;
    try {
      await deleteProfile(id);
      await loadProfiles();
    } catch (err) {
      alert("Error deleting: " + err.message);
    }
  };

  const parseList = (str) => {
    return str.split(',').map(s => s.trim()).filter(Boolean);
  };

  return (
    <div className="container trust-profile-page" style={{ paddingBottom: 'var(--space-8)' }}>
      <div className="page-header">
        <div className="eyebrow">03 · TRUST PROFILE</div>
        <h1 style={{ fontSize: '40px', marginTop: 'var(--space-3)', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <UserCheck size={36} /> Trust Profiles
        </h1>
        <p style={{ color: 'var(--ink-2)', fontSize: '20px', marginTop: 'var(--space-2)' }}>
          Manage user identity and behavioral baselines for anomaly detection.
        </p>
      </div>

      {error ? (
        <ErrorState error={error} onRetry={loadProfiles} />
      ) : isLoading ? (
        <p>Loading profiles...</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: editingProfile ? '1fr 2fr' : '1fr', gap: 'var(--space-6)', alignItems: 'start' }}>
          
          {/* Profile List */}
          <Sheet title="Saved Profiles">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {profiles.length === 0 && <p className="mono" style={{color: 'var(--ink-2)'}}>No profiles found.</p>}
              {profiles.map(p => (
                <div key={p.id} className={`profile-card ${editingProfile?.id === p.id ? 'active' : ''}`} onClick={() => setEditingProfile(p)}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '18px' }}>{p.display_name}</h3>
                      <div className="mono" style={{ fontSize: '13px', color: 'var(--ink-2)', marginTop: '4px' }}>{p.user_id}</div>
                      <div style={{ fontSize: '14px', marginTop: '8px' }}>
                        <span style={{background: 'var(--paper-2)', padding: '2px 8px', borderRadius: '10px'}}>{p.role}</span>
                        {p.demo && <span style={{background: 'var(--allow-bg)', color: 'var(--allow-text)', padding: '2px 8px', borderRadius: '10px', marginLeft: '8px'}}>Demo</span>}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button className="icon-btn" onClick={(e) => { e.stopPropagation(); setEditingProfile(p); }} title="Edit"><Edit2 size={16} /></button>
                      <button className="icon-btn danger" onClick={(e) => { e.stopPropagation(); handleDelete(p.id); }} title="Delete"><Trash2 size={16} /></button>
                    </div>
                  </div>
                </div>
              ))}
              <button className="btn btn-secondary" onClick={handleCreateNew} style={{ marginTop: 'var(--space-2)', justifyContent: 'center' }}>
                <Plus size={16} style={{marginRight: '8px'}} /> Create Profile
              </button>
            </div>
          </Sheet>

          {/* Editor */}
          {editingProfile && (
            <Sheet title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{editingProfile.id.startsWith('usr_') && editingProfile.display_name === 'New Profile' ? 'New Profile' : 'Edit Profile'}</span>
                <button className="icon-btn" onClick={() => setEditingProfile(null)}><X size={20} /></button>
              </div>
            }>
              <div className="profile-editor">
                <div className="editor-section">
                  <h4>Identity Details</h4>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Display Name</label>
                      <input type="text" value={editingProfile.display_name} onChange={e => setEditingProfile({...editingProfile, display_name: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>User ID</label>
                      <input type="text" value={editingProfile.user_id} onChange={e => setEditingProfile({...editingProfile, user_id: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>Role</label>
                      <input type="text" value={editingProfile.role} onChange={e => setEditingProfile({...editingProfile, role: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>Organisation</label>
                      <input type="text" value={editingProfile.organisation} onChange={e => setEditingProfile({...editingProfile, organisation: e.target.value})} />
                    </div>
                  </div>
                  <div className="form-group checkbox">
                    <label>
                      <input type="checkbox" checked={editingProfile.demo} onChange={e => setEditingProfile({...editingProfile, demo: e.target.checked})} />
                      Demo Profile
                    </label>
                  </div>
                </div>

                <div className="editor-section">
                  <h4>Context Baseline</h4>
                  <p className="hint">Comma-separated values for trusted context.</p>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Usual Devices</label>
                      <ListInput placeholder="e.g. iPhone 15, Mac M2" value={editingProfile.baseline.usual_devices} onChange={arr => setEditingProfile({
                        ...editingProfile, baseline: { ...editingProfile.baseline, usual_devices: arr }
                      })} />
                    </div>
                    <div className="form-group">
                      <label>Usual Locations</label>
                      <ListInput placeholder="e.g. Bangalore, Mumbai" value={editingProfile.baseline.usual_locations} onChange={arr => setEditingProfile({
                        ...editingProfile, baseline: { ...editingProfile.baseline, usual_locations: arr }
                      })} />
                    </div>
                    <div className="form-group">
                      <label>Normal Hours (Start - End)</label>
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <input type="number" min="0" max="23" value={editingProfile.baseline.normal_hours.start} onChange={e => setEditingProfile({
                          ...editingProfile, baseline: { ...editingProfile.baseline, normal_hours: { ...editingProfile.baseline.normal_hours, start: parseInt(e.target.value)||0 } }
                        })} />
                        <input type="number" min="0" max="23" value={editingProfile.baseline.normal_hours.end} onChange={e => setEditingProfile({
                          ...editingProfile, baseline: { ...editingProfile.baseline, normal_hours: { ...editingProfile.baseline.normal_hours, end: parseInt(e.target.value)||0 } }
                        })} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label>Trusted Contacts</label>
                      <ListInput placeholder="Account numbers or UPI IDs" value={editingProfile.baseline.trusted_contacts} onChange={arr => setEditingProfile({
                        ...editingProfile, baseline: { ...editingProfile.baseline, trusted_contacts: arr }
                      })} />
                    </div>
                  </div>
                </div>

                <div className="editor-section">
                  <h4>Transaction Patterns</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {editingProfile.baseline.transaction_patterns.length === 0 && <p className="mono hint">No patterns defined.</p>}
                    {editingProfile.baseline.transaction_patterns.map((pt, i) => (
                      <div key={i} className="pattern-card">
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <input type="text" placeholder="Category (e.g. Utility)" value={pt.category} style={{ width: '150px' }} onChange={e => {
                            const pts = [...editingProfile.baseline.transaction_patterns];
                            pts[i].category = e.target.value;
                            setEditingProfile({...editingProfile, baseline: {...editingProfile.baseline, transaction_patterns: pts}});
                          }} />
                          <button className="icon-btn danger" onClick={() => {
                            const pts = [...editingProfile.baseline.transaction_patterns];
                            pts.splice(i, 1);
                            setEditingProfile({...editingProfile, baseline: {...editingProfile.baseline, transaction_patterns: pts}});
                          }}><Trash2 size={16} /></button>
                        </div>
                        <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                          <input type="number" placeholder="Min ₹" value={pt.min_amount} onChange={e => {
                            const pts = [...editingProfile.baseline.transaction_patterns];
                            pts[i].min_amount = parseFloat(e.target.value)||0;
                            setEditingProfile({...editingProfile, baseline: {...editingProfile.baseline, transaction_patterns: pts}});
                          }} />
                          <input type="number" placeholder="Max ₹" value={pt.max_amount} onChange={e => {
                            const pts = [...editingProfile.baseline.transaction_patterns];
                            pts[i].max_amount = parseFloat(e.target.value)||0;
                            setEditingProfile({...editingProfile, baseline: {...editingProfile.baseline, transaction_patterns: pts}});
                          }} />
                        </div>
                        <ListInput placeholder="Typical Payees (comma separated)" value={pt.typical_payees} style={{ marginTop: '10px', width: '100%' }} onChange={arr => {
                          const pts = [...editingProfile.baseline.transaction_patterns];
                          pts[i].typical_payees = arr;
                          setEditingProfile({...editingProfile, baseline: {...editingProfile.baseline, transaction_patterns: pts}});
                        }} />
                      </div>
                    ))}
                    <button className="btn btn-secondary" onClick={() => {
                      const pts = [...editingProfile.baseline.transaction_patterns, {
                        id: `pt_${Date.now()}`, category: 'General', min_amount: 0, max_amount: 1000, typical_payees: [], frequency: 'monthly', usual_days: 'any'
                      }];
                      setEditingProfile({...editingProfile, baseline: {...editingProfile.baseline, transaction_patterns: pts}});
                    }}>
                      <Plus size={14} style={{marginRight: '6px'}} /> Add Pattern
                    </button>
                  </div>
                </div>

                <div className="editor-actions" style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-6)', gap: '12px' }}>
                  <button className="btn btn-secondary" onClick={() => setEditingProfile(null)}>Cancel</button>
                  <button className="btn btn-primary" onClick={handleSave} disabled={isSaving}>
                    <Save size={16} style={{marginRight: '8px'}} /> {isSaving ? 'Saving...' : 'Save Profile'}
                  </button>
                </div>
              </div>
            </Sheet>
          )}
        </div>
      )}
    </div>
  );
}
