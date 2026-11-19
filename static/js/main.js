/**
 * @fileoverview Main application orchestrator and screen wiring for AirPlan.
 */

import { announce, isSpeechSupported, setTextSize, speakText, stopSpeaking, toggleHighContrast, toggleSimpleLanguage } from './a11y.js';
import { t, updateDocumentLang } from './i18n.js';
import { renderAssistantScreen } from './render/assistant.js';
import { renderDetectiveScreen } from './render/detective.js';
import { renderFamilyScreen } from './render/family.js';
import { renderLedgerScreen } from './render/ledger.js';
import { renderNeighbourhoodScreen } from './render/neighbourhood.js';
import { renderResultsScreen } from './render/results.js';
import { getState, setState, subscribe } from './state.js';

function updateControlLabels() {
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
 *
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
 * Switch the currently visible view section and synchronize navigation states.
 *
 * @param {string} screenId - HTML element id of the screen section to show.
 * @returns {void}
 */
export function switchScreen(screenId) {
  const ids = ['family', 'ledger', 'results', 'detective', 'neighbourhood', 'assistant'];
  ids.forEach((name) => {
    const sec = document.getElementById(`screen-${name}`);
    if (sec) sec.hidden = `screen-${name}` !== screenId;
  });
  const stepMap = { 'screen-family': 'step-btn-1', 'screen-ledger': 'step-btn-2', 'screen-results': 'step-btn-3' };
  ['step-btn-1', 'step-btn-2', 'step-btn-3'].forEach((btnId) => {
    const btn = document.getElementById(btnId);
    if (btn) {
      if (stepMap[screenId] === btnId) btn.setAttribute('aria-current', 'step');
      else btn.removeAttribute('aria-current');
    }
  });
}

function bindHeaderControls() {
  document.getElementById('lang-toggle-btn')?.addEventListener('click', () => {
    const next = getState().language === 'en' ? 'hi' : 'en';
    setState({ language: next });
    announce(next === 'hi' ? 'भाषा बदलकर हिंदी की गई' : 'Language changed to English');
  });

  document.getElementById('contrast-toggle-btn')?.addEventListener('click', () => {
    const active = toggleHighContrast();
    setState({ highContrast: active });
  });

  document.getElementById('plain-toggle-btn')?.addEventListener('click', () => {
    const active = toggleSimpleLanguage();
    setState({ simpleLanguage: active });
  });

  document.getElementById('text-size-select')?.addEventListener('change', (e) => {
    const val = e.target.value;
    setTextSize(val);
    setState({ textSize: val });
  });

  const readBtn = document.getElementById('read-aloud-btn');
  if (readBtn) {
    if (!isSpeechSupported()) readBtn.style.display = 'none';
    readBtn.addEventListener('click', () => {
      const s = getState();
      if (s.isSpeaking) {
        stopSpeaking();
        setState({ isSpeaking: false });
      } else {
        const sec = document.querySelector('section.layout-screen:not([hidden])');
        speakText(sec ? (sec.textContent || '').substring(0, 500) : 'AirPlan', s.language);
        setState({ isSpeaking: true });
      }
      updateControlLabels();
    });
  }

  document.getElementById('step-btn-1')?.addEventListener('click', () => switchScreen('screen-family'));
  document.getElementById('step-btn-2')?.addEventListener('click', () => switchScreen('screen-ledger'));
  document.getElementById('step-btn-3')?.addEventListener('click', () => switchScreen('screen-results'));

  const hero = document.getElementById('hero-banner');
  document.getElementById('hero-demo-btn')?.addEventListener('click', () => {
    if (hero) hero.hidden = true;
    setState({ isDemoData: true });
    switchScreen('screen-results');
  });
  document.getElementById('hero-setup-btn')?.addEventListener('click', () => {
    if (hero) hero.hidden = true;
    switchScreen('screen-family');
  });

  const dlg = document.getElementById('settings-dialog');
  document.getElementById('settings-open-btn')?.addEventListener('click', () => dlg?.showModal());
  document.getElementById('settings-close-btn')?.addEventListener('click', () => dlg?.close());

  document.getElementById('screen-family')?.addEventListener('click', (e) => {
    if (e.target.closest('#next-to-ledger-btn')) switchScreen('screen-ledger');
  });

  document.getElementById('subnav-detective-btn')?.addEventListener('click', () => switchScreen('screen-detective'));
  document.getElementById('subnav-neighbourhood-btn')?.addEventListener('click', () => switchScreen('screen-neighbourhood'));
  document.getElementById('subnav-assistant-btn')?.addEventListener('click', () => switchScreen('screen-assistant'));
}

/**
 * Initialize application lifecycle and event listeners.
 *
 * @returns {void}
 */
export function initApp() {
  bindHeaderControls();
  subscribe(() => renderAllScreens());
  renderAllScreens();
  announce('AirPlan ready.');
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initApp);
  else initApp();
}
