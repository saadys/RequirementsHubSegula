/**
 * Segula AI Requirement Hub — API Service Client
 * Connects frontend views to FastAPI backend endpoints at http://localhost:8000/api
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
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
    const contentType = response.headers.get('content-type') || '';
    let data;

    if (contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      data = { detail: text ? text.replace(/<[^>]*>/g, '').trim().slice(0, 200) : `HTTP Error ${response.status}` };
    }

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
  const res = await fetch(`${BASE_URL}/health`);
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

/**
 * Polls the backend every intervalMs until status is no longer PENDING
 * Default timeout is 180s (72 attempts * 2.5s) to accommodate local LLM inference on T4 GPUs
 */
export async function pollSubmissionUntilComplete(requestId, intervalMs = 2500, maxAttempts = 72) {
  let attempts = 0;
  while (attempts < maxAttempts) {
    const result = await fetchSubmissionById(requestId);
    if (result && result.status !== 'PENDING') {
      return result;
    }
    attempts += 1;
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error('Pipeline execution timed out. Please check your submission status in the dashboard.');
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

export async function ingestHistoricProject(requestId, projectData) {
  return request(`/dashboard/${requestId}/ingest-historic`, {
    method: 'POST',
    body: JSON.stringify(projectData),
  });
}
