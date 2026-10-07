export const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8001").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor({ kind, status, code, detail, message }) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

async function request(path, { method = "GET", body, signal, timeoutMs = null } = {}) {
  // Default timeout logic
  if (!timeoutMs) {
    timeoutMs = 15000;
    if (method === "POST" && (path.startsWith("/analyze") || path.startsWith("/challenge/verify"))) {
      timeoutMs = 30000;
    }
  }
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  const combinedSignal = signal ? 
    (signal.aborted ? signal : (
      signal.addEventListener('abort', () => controller.abort()), 
      controller.signal
    )) : controller.signal;

  try {
    const headers = {};
    if (body && !(body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    const options = {
      method,
      headers,
      signal: combinedSignal,
    };

    if (body) {
      options.body = body instanceof FormData ? body : JSON.stringify(body);
    }

    const res = await fetch(`${API_URL}${path.startsWith('/') ? path : '/' + path}`, options);
    clearTimeout(timeoutId);

    const isJson = res.headers.get("content-type")?.includes("application/json");
    let data;
    try {
      data = isJson ? await res.json() : await res.text();
    } catch (e) {
      // Failed to parse body
    }

    if (!res.ok) {
      if (!isJson) {
        throw new ApiError({
          kind: "server",
          status: res.status,
          message: `The backend returned an unexpected response (HTTP ${res.status})`
        });
      }

      let kind = "server";
      if (res.status >= 400 && res.status < 500) kind = "validation";
      
      let code = "unknown";
      let detail = "An error occurred";
      
      if (data) {
        if (data.error) code = data.error;
        if (data.detail) {
          if (Array.isArray(data.detail)) {
            detail = data.detail.map(d => `${d.loc?.[d.loc.length-1] || 'field'}: ${d.msg}`).join("; ");
          } else {
            detail = data.detail;
          }
        }
      }
      
      throw new ApiError({
        kind,
        status: res.status,
        code,
        detail,
        message: detail
      });
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) throw err;
    throw new ApiError({
      kind: "network",
      message: `Cannot reach the TRUSTLOCK backend at ${API_URL}. Check that it is running and that VITE_API_URL matches.`,
      detail: err.message
    });
  }
}

export function friendlyMessage(err) {
  const codeMsgMap = {
    file_too_large: "The file is too large.",
    unsupported_type: "This file type is not supported.",
    empty_file: "The file is empty.",
    unreadable_file: "The file could not be read.",
    challenge_closed: "This challenge is already closed.",
    not_found: "Resource not found.",
    invalid_simulation: "Invalid simulation data.",
    no_challenge_needed: "No challenge is required for this action.",
    unknown_scenario: "The specified scenario is unknown.",
    confirmation_required: "Confirmation is required."
  };
  
  if (err && err.code && codeMsgMap[err.code]) {
    return codeMsgMap[err.code];
  }
  return err?.detail || err?.message || "An unexpected error occurred.";
}

export function normalizeEvidence(record) {
  if (!record) return null;
  const originalName = record.original_name || record.originalName || "";
  const ext = originalName.includes(".") ? originalName.split('.').pop().toLowerCase() : "";
  
  return {
    id: record.id,
    originalName,
    kind: record.kind || "unknown",
    mime: record.mime || "application/octet-stream",
    ext,
    sizeBytes: record.size_bytes !== undefined ? record.size_bytes : (record.sizeBytes || 0),
    sha256: record.sha256 || "",
    uploadedAt: record.uploaded_at || record.uploadedAt || new Date().toISOString(),
    findings: record.findings || [],
    notes: record.notes || ""
  };
}

export async function getHealth(signal) {
  try {
    const res = await request("/health", { signal, timeoutMs: 5000 });
    if (res && res.service === "trustlock") {
      if (res.status === "ok") return { state: "online", reason: null };
      if (res.status === "degraded") return { state: "degraded", reason: "storage" };
    }
    return { state: "offline", reason: "wrong_service" };
  } catch (err) {
    if (err.kind === "network") return { state: "offline", reason: "unreachable" };
    if (err.kind === "server" && err.status) return { state: "offline", reason: "http_error" };
    return { state: "offline", reason: "wrong_service" };
  }
}

export function getConfig() {
  return request("/config");
}

export function getScenarios() {
  return request("/scenarios");
}

export function fetchProfiles() {
  return request("/profiles");
}

export function saveProfile(profile) {
  return request("/profiles", { method: "POST", body: profile });
}

export function deleteProfile(id) {
  return request(`/profiles/${id}`, { method: "DELETE" });
}

export function analyzeAction(payload) {
  return request("/analyze", { method: "POST", body: payload });
}

export function generateChallenge({ case_id, decision }) {
  return request("/challenge/generate", { method: "POST", body: { case_id, decision } });
}

export function getChallenge(challenge_id) {
  return request(`/challenge/${challenge_id}`);
}

export function verifyChallenge({ challenge_id, response, simulation, simulated_outcome, evidence_ids }) {
  return request("/challenge/verify", { method: "POST", body: { challenge_id, response, simulation, simulated_outcome, evidence_ids } });
}

export function getCase(caseId) {
  return request(`/history/${caseId}`);
}

export function getHistory({ decision = "all", limit = 50, offset = 0 } = {}) {
  const qs = new URLSearchParams();
  if (decision !== "all") qs.set("decision", decision);
  qs.set("limit", limit);
  qs.set("offset", offset);
  return request(`/history?${qs.toString()}`);
}

export function resetHistory() {
  return request("/history?confirm=true", { method: "DELETE" });
}

export function verifyLedger() {
  return request("/history/verify");
}

export function deleteEvidence(id) {
  return request(`/evidence/${id}`, { method: "DELETE" });
}

export function evidenceFileUrl(id) {
  return `${API_URL}/evidence/${id}/file`;
}

export function uploadEvidence(file, { onProgress, signal } = {}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    if (signal) {
      if (signal.aborted) {
        return reject(new ApiError({ kind: "network", message: "Upload aborted." }));
      }
      signal.addEventListener('abort', () => xhr.abort());
    }

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(e.loaded / e.total);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res = JSON.parse(xhr.responseText);
          if (res.items && res.items.length > 0) {
            resolve(normalizeEvidence(res.items[0]));
          } else {
            const err = res.errors?.[0] || { msg: "Upload failed" };
            reject(new ApiError({ kind: "validation", code: err.code || "unknown", detail: err.msg, message: err.msg }));
          }
        } catch (e) {
          reject(new ApiError({ kind: "server", message: `The backend returned an unexpected response (HTTP ${xhr.status})` }));
        }
      } else {
        const isJson = xhr.getResponseHeader("content-type")?.includes("application/json");
        if (!isJson) {
          reject(new ApiError({ kind: "server", status: xhr.status, message: `The backend returned an unexpected response (HTTP ${xhr.status})` }));
        } else {
          try {
            const res = JSON.parse(xhr.responseText);
            reject(new ApiError({ kind: xhr.status >= 500 ? "server" : "validation", status: xhr.status, message: res.detail || "Upload failed" }));
          } catch(e) {
            reject(new ApiError({ kind: xhr.status >= 500 ? "server" : "validation", status: xhr.status, message: "Upload failed" }));
          }
        }
      }
    };

    xhr.onerror = () => reject(new ApiError({ kind: "network", message: `Cannot reach the TRUSTLOCK backend at ${API_URL}. Check that it is running and that VITE_API_URL matches.` }));
    xhr.ontimeout = () => reject(new ApiError({ kind: "network", message: `Cannot reach the TRUSTLOCK backend at ${API_URL}. Check that it is running and that VITE_API_URL matches.` }));
    xhr.onabort = () => reject(new ApiError({ kind: "network", message: "Upload aborted." }));

    xhr.open("POST", `${API_URL}/evidence`);
    
    const formData = new FormData();
    formData.append("files", file);
    xhr.send(formData);
  });
}
