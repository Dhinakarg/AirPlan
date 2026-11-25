/**
 * @fileoverview Local-only browser persistence for household settings (never transmitted).
 */

const STORAGE_KEY = 'airplan_household_v1';

/**
 * Load saved household configuration from localStorage safely.
 * @returns {Record<string, any> | null} Saved household fields or null.
 */
export function loadSavedHousehold() {
  try {
    if (typeof localStorage === 'undefined') return null;
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.members)) return null;
    return parsed;
  } catch {
    return null;
  }
}

/**
 * Save current household configuration locally in localStorage.
 * @param {Record<string, any>} state - Current application state.
 * @returns {void}
 */
export function saveHousehold(state) {
  try {
    if (typeof localStorage === 'undefined') return;
    const payload = {
      city: state.city,
      latitude: state.latitude,
      longitude: state.longitude,
      budgetInr: state.budgetInr,
      home: state.home,
      members: state.members,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Ignore storage quota or private browsing errors
  }
}

/**
 * Clear saved household configuration from localStorage.
 * @returns {void}
 */
export function clearSavedHousehold() {
  try {
    if (typeof localStorage === 'undefined') return;
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore storage errors
  }
}
