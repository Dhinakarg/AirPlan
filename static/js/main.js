/**
 * @fileoverview Main application orchestrator and screen wiring for AirLedger.
 */

import {
  announce,
  isSpeechSupported,
  setTextSize,
  speakText,
  stopSpeaking,
  toggleHighContrast,
  toggleSimpleLanguage,
} from './a11y.js';
import { t, updateDocumentLang } from './i18n.js';
import { renderAssistantScreen } from './render/assistant.js';
import { renderDetectiveScreen } from './render/detective.js';
import { renderFamilyScreen } from './render/family.js';
import { renderLedgerScreen } from './render/ledger.js';
import { renderNeighbourhoodScreen } from './render/neighbourhood.js';
import { renderResultsScreen } from './render/results.js';
import { getState, setState, subscribe } from './state.js';

let isSpeaking = false;

/**
 * Render all 6 screens into their respective section containers.
 * @returns {void}
 */
export function renderAllScreens() {
  const screens = [
    ['screen-family', renderFamilyScreen],
    ['screen-ledger', renderLedgerScreen],
    ['screen-results', renderResultsScreen],
    ['screen-detective', renderDetectiveScreen],
    ['screen-neighbourhood', renderNeighbourhoodScreen],
    ['screen-assistant', renderAssistantScreen],
  ];
  screens.forEach(([id, fn]) => {
    const el = document.getElementById(id);
    if (el) fn(el);
  });
  updateControlLabels();
}

/**
 * Update top-level text and control labels on language change.
 * @returns {void}
 */
function updateControlLabels() {
  const lang = getState().language;
  updateDocumentLang(lang);
  const labels = [
    ['site-title-heading', 'siteTitle'],
    ['site-tagline-text', 'siteTagline'],
    ['skip-link-text', 'skipLink'],
    ['lang-btn-text', 'language'],
    ['contrast-btn-text', 'highContrast'],
    ['plain-btn-text', 'plainLanguage'],
    ['tab-family-text', 'navFamily'],
    ['tab-ledger-text', 'navLedger'],
    ['tab-results-text', 'navResults'],
    ['tab-detective-text', 'navDetective'],
    ['tab-neighbourhood-text', 'navNeighbourhood'],
    ['tab-assistant-text', 'navAssistant'],
  ];
  labels.forEach(([id, k]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = t(k, lang);
  });
  const readEl = document.getElementById('read-btn-text');
  if (readEl) readEl.textContent = t(isSpeaking ? 'stopReadAloud' : 'readAloud', lang);
}

/**
 * Switch active visible screen section.
 * @param {string} screenId - Target section container id.
 * @returns {void}
 */
export function switchScreen(screenId) {
  const ids = ['family', 'ledger', 'results', 'detective', 'neighbourhood', 'assistant'];
  ids.forEach((name) => {
    const sec = document.getElementById(`screen-${name}`);
    const tab = document.getElementById(`tab-${name}`);
    const isTarget = `screen-${name}` === screenId;
    if (sec && tab) {
      sec.hidden = !isTarget;
      tab.setAttribute('aria-selected', String(isTarget));
      tab.classList.toggle('active-tab', isTarget);
    }
  });
  announce(`Switched to ${screenId.replace('screen-', '')} view`);
}

/**
 * Attach event listeners to top-level header and navigation controls.
 * @returns {void}
 */
function bindHeaderControls() {
  // Language & visual toggles
  document.getElementById('lang-toggle-btn')?.addEventListener('click', () => {
    const next = getState().language === 'en' ? 'hi' : 'en';
    setState({ language: next });
    announce(`Language: ${next === 'en' ? 'English' : 'Hindi'}`);
  });

  document.getElementById('contrast-toggle-btn')?.addEventListener('click', (e) => {
    const isHc = toggleHighContrast();
    e.currentTarget.setAttribute('aria-pressed', String(isHc));
    setState({ highContrast: isHc });
  });

  document.getElementById('plain-toggle-btn')?.addEventListener('click', (e) => {
    const isPlain = toggleSimpleLanguage();
    e.currentTarget.setAttribute('aria-pressed', String(isPlain));
    setState({ simpleLanguage: isPlain });
  });

  document.getElementById('text-size-select')?.addEventListener('change', (e) => {
    setTextSize(/** @type {any} */ (e.target.value));
    setState({ textSize: e.target.value });
  });

  // Read aloud button
  const readBtn = document.getElementById('read-aloud-btn');
  if (readBtn) {
    if (!isSpeechSupported()) {
      readBtn.style.display = 'none';
    } else {
      readBtn.addEventListener('click', () => {
        if (isSpeaking) {
          stopSpeaking();
          isSpeaking = false;
        } else {
          const sec = document.querySelector('section.layout-screen:not(.sr-only)');
          speakText(sec ? (sec.textContent || '').substring(0, 500) : 'AirLedger', getState().language);
          isSpeaking = true;
        }
        updateControlLabels();
      });
    }
  }

  // Navigation Tabs
  ['family', 'ledger', 'results', 'detective', 'neighbourhood', 'assistant'].forEach((name) => {
    document.getElementById(`tab-${name}`)?.addEventListener('click', () => {
      switchScreen(`screen-${name}`);
    });
  });
}

/**
 * Initialize AirLedger Single Page Application.
 * @returns {void}
 */
export function initApp() {
  bindHeaderControls();
  subscribe(() => renderAllScreens());
  renderAllScreens();
  announce('AirLedger ready.');
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }
}
