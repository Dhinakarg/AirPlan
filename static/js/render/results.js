/**
 * @fileoverview Screen 3: Clean-Air Plan Results, scenarios, commute table, and print/storage controls.
 */

import { announce, showError } from '../a11y.js';
import { createPlan } from '../api.js';
import { el } from '../dom.js';
import { formatConcentration, t } from '../i18n.js';
import { getState, resetState, setState } from '../state.js';
import { renderCommuteTable } from './commute.js';
import { renderTimelineInto } from './timeline.js';

async function runPlanGeneration(s, lang) {
  announce(t('loading', lang));
  setState({ isLoading: true, error: null });
  try {
    const res = await createPlan({
      members: s.members,
      home: s.home,
      latitude: s.latitude,
      longitude: s.longitude,
      budget_inr: s.budgetInr,
      language: lang,
      scenario: s.scenario || 'live',
      commute_distance_km: s.commuteDistanceKm || 8.0,
    });
    const isDemo = res.data_source === 'sample' || String(res.data_source).startsWith('demo:');
    setState({ planResult: res, isDemoData: isDemo, isLoading: false });
    announce('Clean-air plan calculated.');
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Plan calculation failed';
    setState({ isLoading: false, error: msg });
    showError(msg);
  }
}

function buildScenarioBar(s, lang) {
  const bar = el('div', 'actions scenario-bar');
  const scenLbl = el('label', '', `${t('scenarioLabel', lang)}: `);
  scenLbl.htmlFor = 'scenario-select';
  const scenSel = el('select');
  scenSel.id = 'scenario-select';
  [
    ['live', t('scenarioLive', lang)],
    ['severe', t('scenarioSevere', lang)],
    ['moderate', t('scenarioModerate', lang)],
    ['cleaner', t('scenarioCleaner', lang)],
  ].forEach(([val, lbl]) => {
    const opt = Object.assign(el('option', '', lbl), { value: val, selected: s.scenario === val });
    scenSel.appendChild(opt);
  });
  scenSel.addEventListener('change', (e) => setState({ scenario: e.target.value }));

  const genBtn = Object.assign(el('button', 'btn primary btn-primary', `🚀 ${t('generatePlan', lang)}`), { type: 'button' });
  genBtn.addEventListener('click', () => runPlanGeneration(getState(), lang));

  const printBtn = Object.assign(el('button', 'btn btn-secondary', `🖨️ ${t('printPlan', lang)}`), { type: 'button', id: 'print-plan-btn' });
  printBtn.addEventListener('click', () => {
    if (typeof window !== 'undefined' && window.print) window.print();
  });

  const clearBtn = Object.assign(el('button', 'btn btn-secondary', t('clearSavedData', lang)), { type: 'button', id: 'clear-saved-btn' });
  clearBtn.addEventListener('click', () => {
    resetState();
    announce(t('clearSavedData', lang));
  });

  bar.append(scenLbl, scenSel, genBtn, printBtn, clearBtn);
  return bar;
}

/**
 * Render Clean-Air Plan Results screen into container.
 *
 * @param {HTMLElement} container - Target container element.
 * @returns {void}
 */
export function renderResultsScreen(container) {
  container.replaceChildren();
  const s = getState(), lang = s.language;

  container.appendChild(buildScenarioBar(s, lang));
  container.appendChild(el('small', 'help-text', t('localPrivacyNote', lang)));

  const plan = s.planResult;
  if (!plan) return;

  const grid = el('div', 'plan-grid');
  if (s.isDemoData) {
    const demo = el('div', 'demo-banner card grid-col-12', `ℹ️ ${t('demoDataBanner', lang)} (${plan.data_source})`);
    demo.setAttribute('role', 'region');
    demo.setAttribute('aria-label', 'Data Source');
    grid.appendChild(demo);
  }

  // 1. Exposure Index Hero Card
  const firstExp = Object.values(plan.members_exposure)[0];
  const idxAfter = firstExp ? firstExp.index : 70.0;
  const heroCard = el('div', 'card grid-col-12');
  const heroHdr = el('div', 'flex-between', [el('h3', '', 'Household Exposure Index (Before vs After)'), el('span', 'badge', t('illustrative', lang))]);
  const kpis = el('div', 'field-row');
  kpis.append(
    el('div', 'kpi-card', [el('div', 'kpi-val', '100.0'), el('div', 'kpi-label', t('exposureBefore', lang))]),
    el('div', 'kpi-card', [el('div', 'kpi-val', String(idxAfter)), el('div', 'kpi-label', t('exposureAfter', lang))]),
  );
  heroCard.append(heroHdr, kpis, el('p', '', `Mitigation strategies reduce inhaled dose by ${(100 - idxAfter).toFixed(0)}% within monthly limit.`));
  grid.appendChild(heroCard);

  // 2. Three insight cards
  const w = plan.ventilation_window, ww = plan.worst_window;
  grid.append(
    el('div', 'card grid-col-4', [el('h3', '', '🪟 Best time to air'), el('p', '', w ? `${w.start_hour}:00–${w.end_hour}:00` : 'None safe today'), el('small', 'help-text', w ? `Avg PM2.5: ${formatConcentration(w.mean_pm25)}` : 'Keep windows shut during severe smog')]),
    el('div', 'card grid-col-4', [el('h3', '', '⚠️ Worst outdoor time'), el('p', '', ww ? `${ww.start_hour}:00–${ww.end_hour}:00` : '18:00–21:00'), el('small', 'help-text', ww ? `Avg PM2.5: ${formatConcentration(ww.mean_pm25)}` : 'Evening peak traffic and night-time inversion.')]),
    el('div', 'card grid-col-4', [el('h3', '', '🌡️ Atmospheric trap'), el('p', '', plan.inversion?.hours?.length ? 'Active boundary layer inversion' : 'Clear dispersion'), el('small', 'help-text', 'Trapping ground-level particulate matter until midday heating.')]),
  );

  // 3. Top-3 actions
  (plan.ranked_interventions || []).slice(0, 3).forEach((item, i) => {
    const act = item.intervention || item;
    const actCard = el('div', 'card grid-col-4', [el('span', 'badge', `#${i + 1} Action`), el('h3', '', act.title), el('p', '', `Cost: ₹${act.cost_inr_per_month}/mo • Impact: ${(act.impact * 100).toFixed(0)}%`)]);
    actCard.appendChild(el('details', 'impact-receipt', [el('summary', '', `🧾 ${t('impactReceipt', lang)}`), el('p', '', item.why_this_rank), el('p', 'provenance-tag', `${t('assumptions', lang)}: ${act.provenance.text} [Confidence: ${act.provenance.confidence}]`)]));
    grid.appendChild(actCard);
  });

  // 4. Commute Mode Comparison Table + 5. Timeline + 6. Print Disclaimer
  renderCommuteTable(grid, plan.commute_comparison, lang);
  const timeCard = el('div', 'card grid-col-12');
  renderTimelineInto(timeCard, firstExp);
  grid.appendChild(timeCard);
  grid.appendChild(el('p', 'print-only-disclaimer grid-col-12', t('printDisclaimer', lang)));
  container.appendChild(grid);
}
