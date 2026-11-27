/**
 * @fileoverview Screen 3: Auto-generated Clean-Air Plan dashboard, toolbar, and states.
 */

import { announce, showError } from '../a11y.js';
import { createPlan } from '../api.js';
import { el } from '../dom.js';
import { t } from '../i18n.js';
import { getState, resetState, setState } from '../state.js';
import { renderCommuteTable } from './commute.js';
import { computePlanFingerprint, renderInsightsAndActions, renderMemberTabs, renderSkeletonGrid, renderSummaryCard } from './results_cards.js';
import { renderTimelineInto } from './timeline.js';

/**
 * Fetch a fresh clean-air plan from the backend and update state.
 * @param {Record<string, any>} s - Application state.
 * @param {string} lang - Active UI language.
 * @param {string} [fp] - Precomputed input fingerprint.
 * @returns {Promise<void>}
 */
export async function runPlanGeneration(s, lang, fp = computePlanFingerprint(s)) {
  announce(t('loading', lang));
  setState({ isLoading: true, error: null });
  try {
    const res = await createPlan({
      members: s.members, home: s.home, latitude: s.latitude, longitude: s.longitude,
      budget_inr: s.budgetInr, language: lang, scenario: s.scenario || 'live',
      commute_distance_km: s.commuteDistanceKm || 8.0,
    });
    const isDemo = res.data_source === 'sample' || String(res.data_source).startsWith('demo:');
    setState({ planResult: res, planFingerprint: fp, isDemoData: isDemo, isLoading: false, error: null });
    announce('Clean-air plan calculated.');
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Plan calculation failed';
    setState({ isLoading: false, error: msg });
    showError(msg);
  }
}

/**
 * Ensure Step 3 has an up-to-date plan; reuse cached plan if inputs are unchanged.
 * @returns {Promise<void>}
 */
export function ensurePlanGenerated() {
  const s = getState();
  if (s.isLoading) return Promise.resolve();
  const fp = computePlanFingerprint(s);
  if (s.planResult && s.planFingerprint === fp) return Promise.resolve();
  return runPlanGeneration(s, s.language, fp);
}

function buildToolbar(s, lang) {
  const bar = el('div', 'actions scenario-bar toolbar-row');
  const scenLbl = el('label', '', `${t('scenarioLabel', lang)}: `);
  scenLbl.htmlFor = 'scenario-select';
  const scenSel = el('select');
  scenSel.id = 'scenario-select';
  [['live', t('scenarioLive', lang)], ['severe', t('scenarioSevere', lang)], ['moderate', t('scenarioModerate', lang)], ['cleaner', t('scenarioCleaner', lang)]].forEach(([val, lbl]) => {
    scenSel.appendChild(Object.assign(el('option', '', lbl), { value: val, selected: s.scenario === val }));
  });
  scenSel.addEventListener('change', (e) => {
    setState({ scenario: e.target.value }, true);
    runPlanGeneration(getState(), lang);
  });

  const refreshBtn = Object.assign(el('button', 'btn btn-secondary', '🔄 Refresh plan'), { type: 'button', id: 'refresh-plan-btn' });
  refreshBtn.addEventListener('click', () => runPlanGeneration(getState(), lang));
  const printBtn = Object.assign(el('button', 'btn btn-secondary', `🖨️ ${t('printPlan', lang)}`), { type: 'button', id: 'print-plan-btn' });
  printBtn.addEventListener('click', () => { if (typeof window !== 'undefined' && window.print) window.print(); });
  const clearBtn = Object.assign(el('button', 'btn btn-secondary', t('clearSavedData', lang)), { type: 'button', id: 'clear-saved-btn' });
  clearBtn.addEventListener('click', () => { resetState(); announce(t('clearSavedData', lang)); });

  bar.append(scenLbl, scenSel, refreshBtn, printBtn, clearBtn);
  return bar;
}

/**
 * Render Clean-Air Plan Results screen into container.
 * @param {HTMLElement} container - Target container element.
 * @returns {void}
 */
export function renderResultsScreen(container) {
  container.replaceChildren();
  const s = getState(), lang = s.language;
  container.append(buildToolbar(s, lang), el('small', 'help-text', t('localPrivacyNote', lang)));

  if (s.isLoading) { container.appendChild(renderSkeletonGrid()); return; }
  if (s.error) {
    const errCard = el('div', 'card form-error');
    errCard.setAttribute('role', 'alert');
    const retryBtn = Object.assign(el('button', 'btn btn-primary', 'Retry'), { type: 'button', id: 'retry-plan-btn' });
    retryBtn.addEventListener('click', () => runPlanGeneration(getState(), lang));
    errCard.append(el('p', '', `Unable to generate plan: ${s.error}`), retryBtn);
    container.appendChild(errCard);
    return;
  }

  const plan = s.planResult;
  if (!plan) {
    const emptyCard = el('div', 'card');
    const loadBtn = Object.assign(el('button', 'btn btn-primary', 'Retry'), { type: 'button', id: 'retry-plan-btn' });
    loadBtn.addEventListener('click', () => runPlanGeneration(getState(), lang));
    emptyCard.append(el('p', '', 'No plan generated yet for your current household settings.'), loadBtn);
    container.appendChild(emptyCard);
    return;
  }

  const grid = el('div', 'plan-grid');
  if (s.isDemoData) {
    const demo = el('div', 'demo-banner card grid-col-12', `ℹ️ ${t('demoDataBanner', lang)} (${plan.data_source})`);
    demo.setAttribute('role', 'region');
    demo.setAttribute('aria-label', 'Data Source');
    grid.appendChild(demo);
  }

  const names = Object.keys(plan.members_exposure || {});
  const activeName = names.includes(s.selectedResultMember) ? s.selectedResultMember : names[0] || 'Household';
  const activeExp = plan.members_exposure?.[activeName];
  renderMemberTabs(grid, names, activeName);
  renderSummaryCard(grid, activeExp ? activeExp.index : 70.0, activeName, lang);
  renderInsightsAndActions(grid, plan, lang);
  renderCommuteTable(grid, plan.commute_comparison, lang);
  const timeCard = el('div', 'card grid-col-12');
  renderTimelineInto(timeCard, activeExp, lang);
  grid.append(timeCard, el('p', 'print-only-disclaimer grid-col-12', t('printDisclaimer', lang)));
  container.appendChild(grid);
}
