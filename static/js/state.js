/**
 * @fileoverview Reactive application state container. Single source of truth.
 */

/**
 * 5 Pre-configured cities facing seasonal northern Indian winter smog.
 * @type {Record<string, {name: string, lat: number, lon: number}>}
 */
export const PRESET_CITIES = {
  delhi: { name: 'Delhi (NCR)', lat: 28.61, lon: 77.21 },
  gurugram: { name: 'Gurugram (Haryana)', lat: 28.46, lon: 77.03 },
  noida: { name: 'Noida (UP)', lat: 28.53, lon: 77.39 },
  lucknow: { name: 'Lucknow (UP)', lat: 26.85, lon: 80.95 },
  patna: { name: 'Patna (Bihar)', lat: 25.59, lon: 85.14 },
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
  return {
    language: 'en',
    highContrast: false,
    simpleLanguage: false,
    textSize: 'normal',
    city: 'delhi',
    latitude: 28.61,
    longitude: 77.21,
    budgetInr: 500,
    home: {
      leakiness: 'average',
      purifier: false,
      windows_open_hours: [13, 14],
    },
    members: [
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
    simulationResult: null,
    detectiveFindings: null,
    communitySummary: null,
    assistantResult: null,
    isDemoData: false,
    isLoading: false,
    error: null,
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
 * @returns {void}
 */
export function setState(update) {
  Object.assign(state, update);
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
  state = createInitialState();
  subscribers.forEach((listener) => {
    try {
      listener(state);
    } catch {
      // safe fallback
    }
  });
}
