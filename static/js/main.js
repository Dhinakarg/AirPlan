/**
 * @fileoverview Main application orchestrator and screen wiring for AirPlan.
 */

import { announce } from './a11y.js';
import { t, updateDocumentLang } from './i18n.js';
import { bindHeaderControls, switchScreen } from './navigation.js';
import { renderAssistantScreen } from './render/assistant.js';
import { renderDetectiveScreen } from './render/detective.js';
import { renderFamilyScreen } from './render/family.js';
import { renderLedgerScreen } from './render/ledger.js';
import { renderNeighbourhoodScreen } from './render/neighbourhood.js';
import { renderResultsScreen } from './render/results.js';
import { getState, subscribe } from './state.js';

export { switchScreen };

export function updateControlLabels() {
  const s = getState(), lang = s.language;
  updateDocumentLang(lang);
  const labels = [
    ['site-title-heading', 'siteTitle'], ['site-tagline-text', 'siteTagline'], ['skip-link-text', 'skipLink'],
    ['lang-btn-text', 'language'], ['contrast-btn-text', 'highContrast'], ['plain-btn-text', 'plainLanguage'],
    ['step-1-label', 'navFamily'], ['step-2-label', 'navLedger'], ['step-3-label', 'navResults'],
    ['hero-headline', 'heroHeadline'], ['hero-subhead', 'heroSubhead'], ['hero-demo-btn', 'tryDemoFamily'],
    ['hero-setup-btn', 'setUpFamily'], ['settings-btn-text', 'displaySettings'],
  ];
  labels.forEach(([id, k]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = t(k, lang);
  });
  const readEl = document.getElementById('read-btn-text');
  if (readEl) readEl.textContent = t(s.isSpeaking ? 'stopReadAloud' : 'readAloud', lang);
}

/**
 * Render all application screens and synchronize localized UI labels.
 * @returns {void}
 */
export function renderAllScreens() {
  const screens = [
    ['screen-family', renderFamilyScreen], ['screen-ledger', renderLedgerScreen], ['screen-results', renderResultsScreen],
    ['screen-detective', renderDetectiveScreen], ['screen-neighbourhood', renderNeighbourhoodScreen], ['screen-assistant', renderAssistantScreen],
  ];
  screens.forEach(([id, fn]) => {
    const el = document.getElementById(id);
    if (el) fn(el);
  });
  updateControlLabels();
}

/**
 * Initialize application lifecycle and event listeners.
 * @returns {void}
 */
export function initApp() {
  bindHeaderControls(() => updateControlLabels());
  subscribe(() => renderAllScreens());
  renderAllScreens();
  announce('AirPlan ready.');
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initApp);
  else initApp();
}
