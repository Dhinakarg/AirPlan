/**
 * @fileoverview Screen 3: Clean-Air Plan Results, SVG timeline, and Impact Receipts.
 */

import { announce, showError } from '../a11y.js';
import { createPlan } from '../api.js';
import { formatConcentration, getAqiCategory, t } from '../i18n.js';
import { getState, setState } from '../state.js';

function makeKpi(val, label) {
  const card = document.createElement('div');
  card.className = 'kpi-card';
  card.appendChild(document.createElement('div')).className = 'kpi-val';
  card.lastChild.textContent = String(val);
  card.appendChild(document.createElement('div')).className = 'kpi-label';
  card.lastChild.textContent = label;
  return card;
}

/**
 * Render Results Screen.
 * @param {HTMLElement} container - Target container.
 * @returns {void}
 */
export function renderResultsScreen(container) {
  container.replaceChildren();
  const s = getState();
  const lang = s.language;

  const triggerRow = document.createElement('div');
  triggerRow.className = 'form-row';
  const genBtn = document.createElement('button');
  genBtn.type = 'button';
  genBtn.className = 'btn btn-primary btn-large';
  genBtn.textContent = `🚀 ${t('generatePlan', lang)}`;
  genBtn.addEventListener('click', async () => {
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
      });
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

  if (s.isDemoData) {
    const demo = document.createElement('div');
    demo.className = 'demo-banner card';
    demo.setAttribute('role', 'region');
    demo.setAttribute('aria-label', 'Data Source');
    demo.textContent = `ℹ️ ${t('demoDataBanner', lang)}`;
    container.appendChild(demo);
  }

  const firstExp = Object.values(plan.members_exposure)[0];
  const idxAfter = firstExp ? firstExp.index : 70.0;
  const kpiRow = document.createElement('div');
  kpiRow.className = 'kpi-row';
  kpiRow.appendChild(makeKpi('100.0', `${t('exposureBefore', lang)} [${t('illustrative', lang)}]`));
  kpiRow.appendChild(makeKpi(idxAfter, `${t('exposureAfter', lang)} [${t('illustrative', lang)}]`));
  container.appendChild(kpiRow);

  if (plan.ventilation_window) {
    const vc = document.createElement('div');
    vc.className = 'card callout-card';
    const w = plan.ventilation_window;
    vc.appendChild(document.createElement('h3')).textContent =
      `🪟 ${t('ventilationWindow', lang)}: ${w.start_hour}:00–${w.end_hour}:00`;
    vc.appendChild(document.createElement('p')).textContent =
      `${w.rationale} (Avg: ${formatConcentration(w.avg_pm25)})`;
    container.appendChild(vc);
  }

  renderTimeline(container, firstExp);
  renderRanked(container, plan.ranked_interventions, lang);
}

function renderTimeline(container, memberExposure) {
  if (!memberExposure?.hours) return;
  const sec = document.createElement('div');
  sec.className = 'card';
  sec.appendChild(document.createElement('h3')).textContent = '24-Hour Particulate Exposure Timeline';

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 480 160');
  svg.setAttribute('class', 'chart-svg');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', 'Hourly particulate exposure graph across 24 hours');

  const maxVal = Math.max(...memberExposure.hours.map((h) => h.pm25_ug_m3), 300);
  let pathD = '';
  memberExposure.hours.forEach((h, i) => {
    const x = i * 20 + 10;
    const y = 140 - (h.pm25_ug_m3 / maxVal) * 120;
    pathD += (i === 0 ? 'M' : 'L') + `${x},${y}`;
  });
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', pathD);
  path.setAttribute('fill', 'none');
  path.setAttribute('stroke', '#0284c7');
  path.setAttribute('stroke-width', '2');
  svg.appendChild(path);
  sec.appendChild(svg);

  const wrap = document.createElement('div');
  wrap.className = 'table-container';
  const tbl = document.createElement('table');
  const cap = document.createElement('caption');
  cap.textContent = 'Hour-by-hour particulate exposure concentrations and AQI classifications';
  tbl.appendChild(cap);
  const thead = document.createElement('thead');
  const trH = document.createElement('tr');
  ['Hour', 'PM2.5 Conc', 'Inhaled Dose', 'AQI Category'].forEach((h) => {
    const th = document.createElement('th');
    th.scope = 'col';
    th.textContent = h;
    trH.appendChild(th);
  });
  thead.appendChild(trH);
  tbl.appendChild(thead);

  const tbody = document.createElement('tbody');
  memberExposure.hours.forEach((h) => {
    const tr = document.createElement('tr');
    const aqi = getAqiCategory(h.pm25_ug_m3);
    [
      `${h.hour}:00`,
      formatConcentration(h.pm25_ug_m3),
      `${h.dose_ug.toFixed(1)} µg`,
      `${aqi.icon} ${aqi.label} ${aqi.pattern}`,
    ].forEach((val) => {
      tr.appendChild(document.createElement('td')).textContent = val;
    });
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
  wrap.appendChild(tbl);
  sec.appendChild(wrap);
  container.appendChild(sec);
}

function renderRanked(container, interventions, lang) {
  if (!interventions?.length) return;
  const sec = document.createElement('div');
  sec.className = 'card';
  sec.appendChild(document.createElement('h3')).textContent = t('rankedInterventions', lang);
  const list = document.createElement('ol');

  interventions.forEach((item) => {
    const li = document.createElement('li');
    li.className = 'intervention-item';
    const hdr = document.createElement('div');
    hdr.className = 'flex-between';
    hdr.appendChild(document.createElement('strong')).textContent = item.title;
    const bdg = hdr.appendChild(document.createElement('span'));
    bdg.className = 'badge';
    bdg.textContent = `₹${item.cost_inr_per_month}/mo`;
    li.appendChild(hdr);

    const det = document.createElement('details');
    det.className = 'impact-receipt';
    det.appendChild(document.createElement('summary')).textContent =
      `🧾 ${t('impactReceipt', lang)}: ${item.why_this_rank}`;
    det.appendChild(document.createElement('p')).textContent =
      `${t('costPerMonth', lang)}: ₹${item.cost_inr_per_month} • Impact: ${(item.impact * 100).toFixed(0)}%`;
    const p2 = det.appendChild(document.createElement('p'));
    p2.className = 'provenance-tag';
    p2.textContent =
      `${t('assumptions', lang)}: ${item.provenance.text} [${t('confidence', lang)}: ${item.provenance.confidence}]`;
    li.appendChild(det);
    list.appendChild(li);
  });
  sec.appendChild(list);
  container.appendChild(sec);
}
