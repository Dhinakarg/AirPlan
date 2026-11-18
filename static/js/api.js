/**
 * @fileoverview Network API client for communicating with AirLedger backend endpoints.
 */

/**
 * Perform typed JSON fetch with correlation tracking and error handling.
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
 * Fetch operational service health status.
 * @returns {Promise<{status: string, app: string}>}
 */
export async function fetchHealth() {
  return request('/api/health');
}

/**
 * Fetch outdoor 24-hour smog forecast curve.
 * @returns {Promise<{hourly_pm25: number[]}>}
 */
export async function fetchForecast() {
  return request('/api/forecast');
}

/**
 * Fetch catalog of available low-cost interventions.
 * @returns {Promise<Array<any>>}
 */
export async function fetchInterventions() {
  return request('/api/interventions');
}

/**
 * Submit household configuration and generate customized 24-hour plan.
 * @param {Object} profile - Household profile object.
 * @param {'en' | 'hi'} [language='en'] - Output language.
 * @param {string[]} [activeInterventions=[]] - Enabled intervention IDs.
 * @returns {Promise<Object>} CleanAirPlan domain object.
 */
export async function createPlan(profile, language = 'en', activeInterventions = []) {
  return request('/api/plan', {
    method: 'POST',
    body: JSON.stringify({
      profile,
      language,
      active_interventions: activeInterventions,
    }),
  });
}

/**
 * Request plain-language AI explanation for an existing plan.
 * @param {Object} plan - CleanAirPlan domain object.
 * @param {'en' | 'hi'} [language='en'] - Target language.
 * @returns {Promise<{explanation: string}>}
 */
export async function explainPlan(plan, language = 'en') {
  return request('/api/explain', {
    method: 'POST',
    body: JSON.stringify({ plan, language }),
  });
}

