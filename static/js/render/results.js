/**
 * @fileoverview Screen 3: Clean-Air Plan Results, 12-col grid, SVG timeline, and Impact Receipts.
 */

import { announce, showError } from '../a11y.js';
import { createPlan } from '../api.js';
import { el } from '../dom.js';
import { formatConcentration, getAqiCategory, t } from '../i18n.js';
import { getState, setState } from '../state.js';

function renderTimelineInto(sec, memberExposure) {
  if (!memberExposure?.hours) return;
  sec.appendChild(el('h3', '', '24-Hour Particulate Exposure Timeline'));

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 480 160');
  svg.setAttribute('class', 'chart-svg');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', 'Hourly particulate exposure graph across 24 hours');

  const maxVal = Math.max(...memberExposure.hours.map((h) => h.pm25_ug_m3), 300);
  let pathD = '';
  memberExposure.hours.forEach((h, i) => {
    const x = i * 20 + 10, y = 140 - (h.pm25_ug_m3 / maxVal) * 120;
    pathD += (i === 0 ? 'M' : 'L') + `${x},${y}`;
  });
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', pathD);
  path.setAttribute('fill', 'none');
  path.setAttribute('stroke', '#0b7a75');
  path.setAttribute('stroke-width', '3');
  svg.appendChild(path);
  sec.appendChild(svg);

  const wrap = el('div', 'table-container'), tbl = el('table'), cap = el('caption', '', 'Hour-by-hour particulate exposure concentrations and AQI classifications');
  tbl.appendChild(cap);
  const thead = el('thead'), trH = el('tr');
  ['Hour', 'PM2.5 Conc', 'Inhaled Dose', 'AQI Category'].forEach((h) => {
    const th = el('th', '', h); th.scope = 'col'; trH.appendChild(th);
  });
  thead.appendChild(trH);
  tbl.appendChild(thead);

  const tbody = el('tbody');
  memberExposure.hours.forEach((h) => {
    const tr = el('tr'), aqi = getAqiCategory(h.pm25_ug_m3);
    [`${h.hour}:00`, formatConcentration(h.pm25_ug_m3), `${h.dose_ug.toFixed(1)} µg`, `${aqi.icon} ${aqi.label} ${aqi.pattern}`].forEach((val) => {
      tr.appendChild(el('td', '', val));
    });
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
  wrap.appendChild(tbl);
  sec.appendChild(wrap);
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

  const triggerRow = el('div', 'actions');
  const genBtn = el('button', 'btn primary btn-primary', `🚀 ${t('generatePlan', lang)}`);
  genBtn.type = 'button';
  genBtn.addEventListener('click', async () => {
    announce(t('loading', lang));
    setState({ isLoading: true, error: null });
    try {
      const res = await createPlan({ members: s.members, home: s.home, latitude: s.latitude, longitude: s.longitude, budget_inr: s.budgetInr, language: lang });
      setState({ planResult: res, isDemoData: res.data_source === 'sample', isLoading: false });
      announce('Clean-air plan calculated.');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Plan calculation failed';
      setState({ isLoading: false, error: msg });
      showError(msg);
    }
  });
  triggerRow.appendChild(genBtn);
  container.appendChild(triggerRow);

  const plan = s.planResult;
  if (!plan) return;

  const grid = el('div', 'plan-grid');
  if (s.isDemoData) {
    const demo = el('div', 'demo-banner card grid-col-12', `ℹ️ ${t('demoDataBanner', lang)}`);
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
  const kpi1 = el('div', 'kpi-card', [el('div', 'kpi-val', '100.0'), el('div', 'kpi-label', t('exposureBefore', lang))]);
  const kpi2 = el('div', 'kpi-card', [el('div', 'kpi-val', String(idxAfter)), el('div', 'kpi-label', t('exposureAfter', lang))]);
  kpis.append(kpi1, kpi2);
  heroCard.append(heroHdr, kpis, el('p', '', `Mitigation strategies reduce inhaled dose by ${(100 - idxAfter).toFixed(0)}% within monthly limit.`));
  grid.appendChild(heroCard);

  // 2. Three insight cards
  const w = plan.ventilation_window;
  const cVent = el('div', 'card grid-col-4', [el('h3', '', `🪟 Best time to air`), el('p', '', w ? `${w.start_hour}:00–${w.end_hour}:00` : '12:00–14:00'), el('small', 'help-text', w ? `Avg PM2.5: ${formatConcentration(w.avg_pm25)}` : 'Midday smog dispersion')]);
  const cOut = el('div', 'card grid-col-4', [el('h3', '', `⚠️ Worst outdoor time`), el('p', '', '18:00–21:00 & 06:00–08:00'), el('small', 'help-text', 'Evening peak traffic combined with night-time inversion.')]);
  const cInv = el('div', 'card grid-col-4', [el('h3', '', `🌡️ Atmospheric trap`), el('p', '', 'Active boundary layer inversion'), el('small', 'help-text', 'Trapping ground-level particulate matter until midday heating.')]);
  grid.append(cVent, cOut, cInv);

  // 3. Top-3 actions
  const topActions = (plan.ranked_interventions || []).slice(0, 3);
  topActions.forEach((item, i) => {
    const actCard = el('div', 'card grid-col-4', [el('span', 'badge', `#${i + 1} Action`), el('h3', '', item.title), el('p', '', `Cost: ₹${item.cost_inr_per_month}/mo • Impact: ${(item.impact * 100).toFixed(0)}%`)]);
    const det = el('details', 'impact-receipt', [el('summary', '', `🧾 ${t('impactReceipt', lang)}`), el('p', '', item.why_this_rank), el('p', 'provenance-tag', `${t('assumptions', lang)}: ${item.provenance.text} [Confidence: ${item.provenance.confidence}]`)]);
    actCard.appendChild(det);
    grid.appendChild(actCard);
  });

  // 4. Timeline chart
  const timeCard = el('div', 'card grid-col-12');
  renderTimelineInto(timeCard, firstExp);
  grid.appendChild(timeCard);

  container.appendChild(grid);
}
