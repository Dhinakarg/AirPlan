/**
 * @fileoverview Reactive application state container. Single source of truth.
 */

import { clearSavedHousehold, loadSavedHousehold, saveHousehold } from './storage.js';

export const PRESET_CITIES = {
  delhi: { name: 'Delhi (NCR)', lat: 28.61, lon: 77.21 }, gurugram: { name: 'Gurugram (Haryana)', lat: 28.46, lon: 77.03 },
  noida: { name: 'Noida (UP)', lat: 28.53, lon: 77.39 }, ghaziabad: { name: 'Ghaziabad (UP)', lat: 28.67, lon: 77.45 },
  faridabad: { name: 'Faridabad (Haryana)', lat: 28.41, lon: 77.31 }, lucknow: { name: 'Lucknow (UP)', lat: 26.85, lon: 80.95 },
  kanpur: { name: 'Kanpur (UP)', lat: 26.45, lon: 80.33 }, patna: { name: 'Patna (Bihar)', lat: 25.59, lon: 85.14 },
  jaipur: { name: 'Jaipur (Rajasthan)', lat: 26.91, lon: 75.79 }, chandigarh: { name: 'Chandigarh', lat: 30.73, lon: 76.78 },
  kolkata: { name: 'Kolkata (WB)', lat: 22.57, lon: 88.36 }, mumbai: { name: 'Mumbai (MH)', lat: 19.08, lon: 72.88 },
  bengaluru: { name: 'Bengaluru (KA)', lat: 12.97, lon: 77.59 }, hyderabad: { name: 'Hyderabad (TS)', lat: 17.38, lon: 78.49 },
  chennai: { name: 'Chennai (TN)', lat: 13.08, lon: 80.27 },
};

/**
 * Default standard baseline routine blocks.
 * @type {Array<{start_hour: number, end_hour: number, activity: string, mode: string}>}
 */
export const DEFAULT_ROUTINE = [
  { start_hour: 0, end_hour: 7, activity: 'sleep', mode: 'home' },
  { start_hour: 7, end_hour: 8, activity: 'cook', mode: 'home' },
  { start_hour: 8, end_hour: 9, activity: 'walk', mode: 'walk' },
  { start_hour: 9, end_hour: 17, activity: 'light', mode: 'home' },
  { start_hour: 17, end_hour: 18, activity: 'exercise', mode: 'outdoor' },
  { start_hour: 18, end_hour: 22, activity: 'rest', mode: 'home' },
  { start_hour: 22, end_hour: 24, activity: 'sleep', mode: 'home' },
];

/**
 * Factory for initial application state.
 * @returns {Record<string, any>} Initialized state object.
 */
function createInitialState() {
  const saved = loadSavedHousehold();
  return {
    language: 'en',
    highContrast: false,
    simpleLanguage: false,
    textSize: 'normal',
    city: saved?.city || 'delhi',
    latitude: saved?.latitude ?? 28.61,
    longitude: saved?.longitude ?? 77.21,
    budgetInr: saved?.budgetInr ?? 500,
    homeSelected: Boolean(saved?.homeSelected), citySelected: Boolean(saved?.citySelected), budgetSelected: Boolean(saved?.budgetSelected),
    homeBudgetOpen: false,
    scenario: 'live',
    commuteDistanceKm: 8.0,
    home: saved?.home || {
      leakiness: 'average',
      purifier: false,
      windows_open_hours: [13, 14],
    },
    members: saved?.members || [
      {
        name: 'Aarav',
        age_group: 'child',
        sensitivity: 'asthma_or_heart',
        routine: JSON.parse(JSON.stringify(DEFAULT_ROUTINE)),
      },
      {
        name: 'Sunita',
        age_group: 'adult',
        sensitivity: 'none',
        routine: JSON.parse(JSON.stringify(DEFAULT_ROUTINE)),
      },
    ],
    activeMemberIndex: 0,
    planResult: null,
    planFingerprint: null,
    selectedResultMember: null,
    showTimelineTable: false,
    simulationResult: null,
    detectiveFindings: null,
    communitySummary: null,
    assistantResult: null,
    isDemoData: false,
    isLoading: false,
    error: null,
    isSpeaking: false,
  };
}

let state = createInitialState();
const subscribers = new Set();

/**
 * Retrieve current snapshot of immutable state.
 * @returns {Record<string, any>} State snapshot.
 */
export function getState() {
  return state;
}

/**
 * Update state slice and notify all registered subscribers.
 * @param {Record<string, any>} update - Partial state update.
 * @param {boolean} [silent=false] - Skip subscriber re-render when updating in-place.
 * @returns {void}
 */
export function setState(update, silent = false) {
  Object.assign(state, update);
  saveHousehold(state);
  if (silent) return;
  subscribers.forEach((listener) => {
    try {
      listener(state);
    } catch (err) {
      if (typeof console !== 'undefined' && console.error) {
        console.error('State subscriber error', err);
      }
    }
  });
}

/**
 * Subscribe a callback to state changes.
 * @param {function(Record<string, any>): void} listener - Listener callback.
 * @returns {function(): void} Unsubscribe function.
 */
export function subscribe(listener) {
  subscribers.add(listener);
  return () => {
    subscribers.delete(listener);
  };
}

/**
 * Reset application state to initial defaults.
 * @returns {void}
 */
export function resetState() {
  clearSavedHousehold();
  state = createInitialState();
  subscribers.forEach((listener) => {
    try {
      listener(state);
    } catch {
      // safe fallback
    }
  });
}
