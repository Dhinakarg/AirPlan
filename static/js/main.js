/**
 * @fileoverview Main application bootstrapper and orchestrator for AirLedger.
 */

import { announce, toggleHighContrast } from './a11y.js';
import { createPlan } from './api.js';
import { t } from './i18n.js';
import { renderInterventions } from './render/interventions.js';
import { renderMembers } from './render/members.js';
import { renderSources } from './render/sources.js';
import { renderSummaryCards } from './render/summary.js';
import { renderTimeline } from './render/timeline.js';
import { getState, setState, subscribe } from './state.js';

/**
 * Recalculate plan based on current state parameters.
 * @returns {Promise<void>}
 */
async function refreshPlan() {
  const s = getState();
  setState({ isLoading: true });
  announce(t('loading', s.language));

  try {
    const plan = await createPlan(s.householdProfile, s.language, s.activeInterventions);
    setState({ currentPlan: plan, isLoading: false, error: null });
    announce('Clean air plan updated successfully.');
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Calculation error';
    setState({ isLoading: false, error: msg });
    announce(`Error: ${msg}`, 'assertive');
  }
}

/**
 * Handle user toggling an intervention checkbox.
 * @param {string} id - Intervention identifier.
 * @param {boolean} active - Checkbox state.
 * @returns {void}
 */
function handleInterventionToggle(id, active) {
  const current = new Set(getState().activeInterventions);
  if (active) {
    current.add(id);
  } else {
    current.delete(id);
  }
  setState({ activeInterventions: Array.from(current) });
  refreshPlan();
}

/**
 * Update UI text elements based on active language dictionary.
 * @param {'en' | 'hi'} lang - Language code.
 * @returns {void}
 */
function updateLocalization(lang) {
  const elements = [
    ['site-title-heading', 'siteTitle'],
    ['site-tagline-text', 'siteTagline'],
    ['form-title-text', 'householdProfile'],
    ['label-fuel', 'cookingFuel'],
    ['label-exhaust', 'exhaustFan'],
    ['label-incense', 'incenseCoils'],
    ['label-sealing', 'sealingDrafts'],
    ['label-volume', 'roomVolume'],
    ['label-cadr', 'purifierCadr'],
    ['calculate-btn-text', 'generatePlan'],
    ['kpi-reduction-label', 'exposureReduction'],
    ['kpi-indoor-label', 'indoorAvg'],
    ['kpi-peak-label', 'smogAlert'],
    ['sources-title-text', 'sourcesTitle'],
    ['interventions-title-text', 'interventionsTitle'],
    ['timeline-title-text', 'timelineTitle'],
    ['members-title-text', 'membersTitle'],
    ['contrast-btn-text', 'highContrast'],
    ['plain-btn-text', 'plainLanguage'],
  ];

  elements.forEach(([id, key]) => {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = t(key, lang);
    }
  });

  const langBtnText = document.getElementById('lang-btn-text');
  if (langBtnText) {
    langBtnText.textContent = lang === 'en' ? 'हिंदी' : 'English';
  }
}

/**
 * Initialize event listeners on controls and forms.
 * @returns {void}
 */
function bindEventListeners() {
  const form = document.getElementById('profile-form');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const s = getState();
      const fuel = /** @type {HTMLSelectElement} */ (document.getElementById('cooking-fuel-select')).value;
      const hasExhaust = /** @type {HTMLInputElement} */ (document.getElementById('exhaust-fan-chk')).checked;
      const hasIncense = /** @type {HTMLInputElement} */ (document.getElementById('incense-chk')).checked;
      const windowsSealed = /** @type {HTMLInputElement} */ (document.getElementById('sealing-chk')).checked;
      const volume = parseFloat(/** @type {HTMLInputElement} */ (document.getElementById('volume-input')).value) || 60;
      const cadr = parseFloat(/** @type {HTMLInputElement} */ (document.getElementById('purifier-cadr-input')).value) || 0;

      const updatedProfile = {
        ...s.householdProfile,
        cooking_fuel: fuel,
        has_exhaust_fan: hasExhaust,
        has_incense_or_coils: hasIncense,
        windows_sealed: windowsSealed,
        room_volume_m3: volume,
        purifier_cadr_m3h: cadr,
      };
      setState({ householdProfile: updatedProfile });
      refreshPlan();
    });
  }

  const langBtn = document.getElementById('lang-toggle-btn');
  if (langBtn) {
    langBtn.addEventListener('click', () => {
      const nextLang = getState().language === 'en' ? 'hi' : 'en';
      setState({ language: nextLang });
      updateLocalization(nextLang);
      refreshPlan();
    });
  }

  const contrastBtn = document.getElementById('contrast-toggle-btn');
  if (contrastBtn) {
    contrastBtn.addEventListener('click', () => {
      const isHigh = toggleHighContrast();
      contrastBtn.setAttribute('aria-pressed', String(isHigh));
    });
  }

  const plainBtn = document.getElementById('plain-toggle-btn');
  if (plainBtn) {
    plainBtn.addEventListener('click', () => {
      const next = !getState().plainLanguage;
      setState({ plainLanguage: next });
      plainBtn.setAttribute('aria-pressed', String(next));
      renderSummaryCards(getState().currentPlan, next);
    });
  }
}

/**
 * Global subscriber rerendering UI components on state change.
 * @param {import('./state.js').AppState} s - Current state.
 * @returns {void}
 */
function onStateChange(s) {
  if (!s.currentPlan) return;

  renderSummaryCards(s.currentPlan, s.plainLanguage);

  const sourcesBox = document.getElementById('sources-list-container');
  if (sourcesBox) renderSources(sourcesBox, s.currentPlan.identified_sources);

  const itBox = document.getElementById('interventions-list-container');
  if (itBox) renderInterventions(itBox, s.currentPlan.ranked_interventions, handleInterventionToggle);

  const chartBox = document.getElementById('chart-container');
  const tableBody = document.getElementById('hourly-table-body');
  if (chartBox && tableBody) renderTimeline(chartBox, tableBody, s.currentPlan);

  const membersBox = document.getElementById('members-container');
  if (membersBox) renderMembers(membersBox, s.currentPlan.member_plans);
}

// Subscribe to reactive state updates and start application
subscribe(onStateChange);
bindEventListeners();
refreshPlan();

