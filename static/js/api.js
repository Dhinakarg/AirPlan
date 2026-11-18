/**
 * @fileoverview Network API client for communicating with AirPlan backend endpoints.
 */

/**
 * Perform typed JSON fetch with correlation tracking and domain error extraction.
 * @param {string} url - Target URL.
 * @param {RequestInit} [options={}] - Standard fetch options.
 * @returns {Promise<any>} Parsed response data.
 */
async function request(url, options = {}) {
  const correlationId = 'web-' + Math.random().toString(36).substring(2, 10);
  const headers = {
    'Content-Type': 'application/json',
    'X-Correlation-ID': correlationId,
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let errBody = {};
    try {
      errBody = await response.json();
    } catch {
      // Empty or non-JSON response body
    }
    const message = errBody.error || `HTTP ${response.status}: Request failed`;
    throw new Error(message);
  }
  return response.json();
}

/**
 * Operational service healthcheck.
 * @returns {Promise<{status: string}>}
 */
export async function fetchHealth() {
  return request('/api/v1/health');
}

/**
 * Submit household configuration and generate customized 24-hour plan.
 * @param {Record<string, any>} payload - PlanRequest payload.
 * @returns {Promise<Record<string, any>>} PlanResponse domain object.
 */
export async function createPlan(payload) {
  return request('/api/v1/plan', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Simulate counterfactual daily routine adjustments.
 * @param {Record<string, any>} payload - SimulateRequest payload.
 * @returns {Promise<Record<string, any>>} RoutineComparison object.
 */
export async function simulateRoutine(payload) {
  return request('/api/v1/simulate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Diagnose domestic pollution emission sources from survey.
 * @param {Record<string, any>} payload - HomeAnalyzeRequest questionnaire.
 * @returns {Promise<{findings: Array<any>}>} HomeAnalyzeResponse.
 */
export async function analyzeHome(payload) {
  return request('/api/v1/home/analyze', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Submit privacy-preserving community clean-air action pledge.
 * @param {{area_code: string, action: string, count: number}} payload - PledgeRequest.
 * @returns {Promise<{status: string, message: string, area_code: string}>}
 */
export async function submitPledge(payload) {
  return request('/api/v1/community/pledges', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Retrieve aggregated community metrics and emissions savings.
 * @param {string} [areaCode] - Optional coarse geographic code.
 * @returns {Promise<Record<string, any>>} CommunityImpact metrics.
 */
export async function fetchCommunitySummary(areaCode) {
  const query = areaCode ? `?area_code=${encodeURIComponent(areaCode)}` : '';
  return request(`/api/v1/community/summary${query}`);
}

/**
 * Inquire with guarded clean-air assistant.
 * @param {string} question - User question text.
 * @param {Record<string, any>} [facts={}] - Ground truth calculation facts.
 * @param {'en' | 'hi'} [language='en'] - Preferred language.
 * @returns {Promise<Record<string, any>>} AskResponse.
 */
export async function askAssistant(question, facts = {}, language = 'en') {
  return request('/api/v1/ask', {
    method: 'POST',
    body: JSON.stringify({ question, facts, language }),
  });
}
