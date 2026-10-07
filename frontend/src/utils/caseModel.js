export const createEmptyCase = () => ({
  scenario_id: null,
  profile_id: null,
  identity: {
    claimed_name: "",
    claimed_role: "",
    credential_verified: false,
    face_match: 0,
    voice_match: 0,
    liveness_ok: false,
    document_tampered: false,
    sources: {}
  },
  context: {
    known_device: false,
    location_matches_pattern: false,
    remote_access_tool: false,
    local_hour: 12,
    sources: {}
  },
  behavior: {
    urgency: "low",
    pressure_language: false,
    skipped_verification_steps: false,
    unusual_session_behavior: false,
    sources: {}
  },
  transaction: {
    action_type: "fund_transfer",
    amount_inr: 0,
    usual_amount_inr: 0,
    recipient_label: "",
    new_recipient: false,
    recipient_account_age_days: 0,
    tx_last_hour: 0,
    sources: {}
  },
  evidence_ids: []
});

export const loadScenario = (scenario) => {
  if (!scenario || !scenario.payload) return createEmptyCase();
  const base = createEmptyCase();
  
  // Create a deep copy to avoid mutations
  return {
    ...base,
    scenario_id: scenario.id || null,
    profile_id: scenario.payload.profile_id || null,
    identity: { ...base.identity, ...(scenario.payload.identity || {}) },
    context: { ...base.context, ...(scenario.payload.context || {}) },
    behavior: { ...base.behavior, ...(scenario.payload.behavior || {}) },
    transaction: { ...base.transaction, ...(scenario.payload.transaction || {}) },
    evidence_ids: [...(scenario.payload.evidence_ids || [])]
  };
};

export const updateField = (caseState, section, field, value) => {
  return {
    ...caseState,
    [section]: {
      ...caseState[section],
      [field]: value
    }
  };
};

export const addEvidenceId = (caseState, evidenceId) => {
  if (caseState.evidence_ids.includes(evidenceId)) return caseState;
  return {
    ...caseState,
    evidence_ids: [...caseState.evidence_ids, evidenceId]
  };
};

export const removeEvidenceId = (caseState, evidenceId) => {
  return {
    ...caseState,
    evidence_ids: caseState.evidence_ids.filter(id => id !== evidenceId)
  };
};
