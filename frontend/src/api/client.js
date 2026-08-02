/**
 * Segula AI Requirement Hub — API Service Client
 * Connects frontend views to FastAPI backend endpoints at http://localhost:8000/api
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const ROOT_URL = BASE_URL.replace(/\/api\/?$/, '');

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const defaultHeaders = {};

  if (options.body && !(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || `HTTP Error ${response.status}`);
    }
    return data;
  } catch (error) {
    console.error(`[API Error] ${endpoint}:`, error);
    throw error;
  }
}

// -------------------------------------------------------------
// Health Check
// -------------------------------------------------------------
export async function fetchHealth() {
  const res = await fetch(`${ROOT_URL}/health`);
  return res.json();
}

// -------------------------------------------------------------
// Module A: Departments & Form Metadata
// -------------------------------------------------------------
export async function fetchDepartments() {
  return request('/departments/');
}

export async function fetchDepartmentById(departmentId) {
  return request(`/departments/${departmentId}`);
}

export async function fetchDepartmentFields(departmentId) {
  return request(`/departments/${departmentId}/fields`);
}

// -------------------------------------------------------------
// Module B: Core Submissions
// -------------------------------------------------------------
export async function submitRequest(submissionPayload) {
  return request('/submissions/', {
    method: 'POST',
    body: JSON.stringify(submissionPayload),
  });
}

export async function submitRequestWithUpload(formData) {
  return request('/submissions/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function fetchSubmissions(params = {}) {
  const query = new URLSearchParams(params).toString();
  return request(`/submissions/${query ? `?${query}` : ''}`);
}

export async function fetchSubmissionById(requestId) {
  return request(`/submissions/${requestId}`);
}

// -------------------------------------------------------------
// Module C: Clarification Loop
// -------------------------------------------------------------
export async function fetchClarification(requestId) {
  return request(`/submissions/${requestId}/clarification`);
}

export async function submitClarification(requestId, answersList) {
  return request(`/submissions/${requestId}/clarification`, {
    method: 'POST',
    body: JSON.stringify({ answers: answersList }),
  });
}

// -------------------------------------------------------------
// Module D: Reports & Scores
// -------------------------------------------------------------
export async function fetchReport(requestId) {
  return request(`/submissions/${requestId}/report`);
}

export async function fetchScore(requestId) {
  return request(`/submissions/${requestId}/score`);
}

// -------------------------------------------------------------
// Module E: AI Team Dashboard
// -------------------------------------------------------------
export async function fetchPendingDashboard(statusFilter = null) {
  const query = statusFilter ? `?status_filter=${statusFilter}` : '';
  return request(`/dashboard/pending${query}`);
}

export async function overrideDecision(requestId, { decision, reviewer_notes, reviewer_name }) {
  return request(`/dashboard/${requestId}/decision`, {
    method: 'POST',
    body: JSON.stringify({ decision, reviewer_notes, reviewer_name }),
  });
}
