/**
 * @fileoverview Reactive application state container. Single source of truth.
 */

/**
 * @typedef {Object} AppState
 * @property {'en' | 'hi'} language
 * @property {boolean} highContrast
 * @property {boolean} plainLanguage
 * @property {Object} householdProfile
 * @property {string[]} activeInterventions
 * @property {Object|null} currentPlan
 * @property {boolean} isLoading
 * @property {string|null} error
 */

/** @type {AppState} */
const state = {
  language: 'en',
  highContrast: false,
  plainLanguage: false,
  householdProfile: {
    home_type: 'apartment',
    cooking_fuel: 'lpg',
    cooking_hours: [7, 8, 19, 20],
    has_exhaust_fan: false,
    has_air_purifier: false,
    purifier_cadr_m3h: 0.0,
    room_volume_m3: 60.0,
    has_incense_or_coils: true,
    incense_hours: [6, 18],
    has_smokers: false,
    windows_sealed: false,
    members: [
      {
        id: 'member-1',
        name: 'Aarav (Child)',
        age_group: 'child',
        health_conditions: ['asthma'],
        routine: [],
      },
      {
        id: 'member-2',
        name: 'Sunita (Elderly)',
        age_group: 'elderly',
        health_conditions: ['copd'],
        routine: [],
      },
    ],
  },
  activeInterventions: ['diy_box_filter', 'window_weatherstripping', 'n95_outdoor_respirator'],
  currentPlan: null,
  isLoading: false,
  error: null,
};

/** @type {Set<function(AppState): void>} */
const subscribers = new Set();

/**
 * Retrieve current snapshot of immutable state.
 * @returns {AppState} State snapshot.
 */
export function getState() {
  return state;
}

/**
 * Update state slice and notify all registered subscribers.
 * @param {Partial<AppState>} update - Partial state update.
 * @returns {void}
 */
export function setState(update) {
  Object.assign(state, update);
  subscribers.forEach((listener) => {
    try {
      listener(state);
    } catch (err) {
      // Prevent listener errors from breaking other subscribers
      if (typeof console !== 'undefined' && console.error) {
        console.error('State subscriber error', err);
      }
    }
  });
}

/**
 * Subscribe a callback to state changes.
 * @param {function(AppState): void} listener - Listener callback.
 * @returns {function(): void} Unsubscribe function.
 */
export function subscribe(listener) {
  subscribers.add(listener);
  return () => {
    subscribers.delete(listener);
  };
}

