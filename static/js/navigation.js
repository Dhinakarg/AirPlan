/**
 * @fileoverview Navigation, screen switching, and header event binding.
 */

import { announce, isSpeechSupported, setTextSize, speakText, stopSpeaking, toggleHighContrast, toggleSimpleLanguage } from './a11y.js';
import { ensurePlanGenerated } from './render/results.js';
import { DEFAULT_ROUTINE, getState, setState } from './state.js';

/**
 * Switch the currently visible view section and synchronize navigation states.
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
  const subMap = { 'screen-detective': 'subnav-detective-btn', 'screen-neighbourhood': 'subnav-neighbourhood-btn', 'screen-assistant': 'subnav-assistant-btn' };
  Object.values(subMap).forEach((btnId) => {
    document.getElementById(btnId)?.classList.toggle('active-sub', subMap[screenId] === btnId);
  });
  if (typeof window !== 'undefined' && window.scrollTo) {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  if (screenId === 'screen-results') {
    ensurePlanGenerated();
  }
}

/**
 * Wire interactive click and change listeners to header controls.
 * @param {() => void} onLabelChange - Callback to re-synchronize localized labels.
 * @returns {void}
 */
export function bindHeaderControls(onLabelChange) {
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
      onLabelChange();
    });
  }

  document.getElementById('step-btn-1')?.addEventListener('click', () => switchScreen('screen-family'));
  document.getElementById('step-btn-2')?.addEventListener('click', () => switchScreen('screen-ledger'));
  document.getElementById('step-btn-3')?.addEventListener('click', () => switchScreen('screen-results'));

  const hero = document.getElementById('hero-banner');
  document.getElementById('hero-demo-btn')?.addEventListener('click', () => {
    if (hero) hero.hidden = true;
    setState({
      city: 'delhi', latitude: 28.61, longitude: 77.21, budgetInr: 800,
      home: { leakiness: 'average', purifier: false, windows_open_hours: [13, 14] },
      homeSelected: true, citySelected: true, budgetSelected: true,
      scenario: 'moderate', isDemoData: true, planFingerprint: null,
      members: [
        { name: 'Aarav', age_group: 'child', sensitivity: 'asthma_or_heart', routine: JSON.parse(JSON.stringify(DEFAULT_ROUTINE)) },
        { name: 'Sunita', age_group: 'adult', sensitivity: 'none', routine: JSON.parse(JSON.stringify(DEFAULT_ROUTINE)) },
      ],
    });
    switchScreen('screen-results');
  });
  document.getElementById('hero-setup-btn')?.addEventListener('click', () => {
    if (hero) hero.hidden = true;
    switchScreen('screen-family');
    document.getElementById('open-add-member-btn')?.focus();
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

