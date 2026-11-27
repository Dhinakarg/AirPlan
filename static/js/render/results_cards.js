/**
 * @fileoverview Card & skeleton builders for the Clean-Air Plan dashboard.
 */

import { el } from '../dom.js';
import { formatConcentration, t } from '../i18n.js';
import { setState } from '../state.js';

/**
 * Compute deterministic fingerprint of plan inputs to detect changes.
 * @param {Record<string, any>} s - Application state.
 * @returns {string} Serialized input signature.
 */
export function computePlanFingerprint(s) {
  return JSON.stringify({
    m: s.members, h: s.home, lat: s.latitude, lon: s.longitude,
    b: s.budgetInr, sc: s.scenario, l: s.language, d: s.commuteDistanceKm,
  });
}

/**
 * Render aria-live loading skeleton while plan API request is in flight.
 * @returns {HTMLElement} Skeleton grid container.
 */
export function renderSkeletonGrid() {
  const skel = el('div', 'plan-grid');
  skel.id = 'plan-loading-skeleton';
  skel.setAttribute('aria-live', 'polite');
  skel.setAttribute('role', 'status');
  skel.setAttribute('aria-busy', 'true');
  skel.appendChild(el('span', 'sr-only', 'Generating your clean-air plan...'));

  const heroSkel = el('div', 'card grid-col-12');
  heroSkel.append(el('div', 'skeleton'), el('div', 'skeleton'));
  skel.appendChild(heroSkel);
  for (let i = 0; i < 3; i += 1) {
    const c = el('div', 'card grid-col-4');
    c.append(el('div', 'skeleton'), el('div', 'skeleton'));
    skel.appendChild(c);
  }
  return skel;
}

/**
 * Render per-member selector tabs when household has multiple members.
 * @param {HTMLElement} grid - Target plan grid.
 * @param {string[]} names - Member names.
 * @param {string} activeName - Selected member name.
 * @returns {void}
 */
export function renderMemberTabs(grid, names, activeName) {
  if (names.length <= 1) return;
  const bar = el('div', 'member-tabs grid-col-12');
  bar.setAttribute('role', 'tablist');
  bar.setAttribute('aria-label', 'Per-member results');
  names.forEach((name) => {
    const isSel = name === activeName;
    const btn = Object.assign(
      el('button', `btn ${isSel ? 'btn-primary' : 'btn-secondary'}`, name),
      { type: 'button' },
    );
    btn.setAttribute('role', 'tab');
    btn.setAttribute('aria-selected', String(isSel));
    btn.addEventListener('click', () => setState({ selectedResultMember: name }));
    bar.appendChild(btn);
  });
  grid.appendChild(bar);
}

/**
 * Render full-width Exposure Index summary card and one-line disclaimer.
 * @param {HTMLElement} grid - Target plan grid.
 * @param {number} idxAfter - Mitigated exposure index.
 * @param {string} memberName - Active member name.
 * @param {string} lang - Active UI language.
 * @returns {void}
 */
export function renderSummaryCard(grid, idxAfter, memberName, lang) {
  const heroCard = el('div', 'card grid-col-12');
  const heroHdr = el('div', 'flex-between', [
    el('h3', '', `Exposure Index — ${memberName}`),
    el('span', 'badge', t('illustrative', lang)),
  ]);
  const kpis = el('div', 'field-row');
  kpis.append(
    el('div', 'kpi-card', [el('div', 'kpi-val', '100.0'), el('div', 'kpi-label', t('exposureBefore', lang))]),
    el('div', 'kpi-card', [el('div', 'kpi-val', String(idxAfter)), el('div', 'kpi-label', t('exposureAfter', lang))]),
  );
  const pct = Math.max(0, 100 - idxAfter).toFixed(0);
  heroCard.append(heroHdr, kpis, el('p', '', `Your plan lowers estimated exposure by ${pct}%.`));
  grid.append(heroCard, el('p', 'provenance-tag grid-col-12', t('printDisclaimer', lang)));
}

/**
 * Render the 3 equal meteorological insight cards and ranked top action cards.
 * @param {HTMLElement} grid - Target plan grid.
 * @param {Record<string, any>} plan - PlanResponse payload.
 * @param {string} lang - Active UI language.
 * @returns {void}
 */
export function renderInsightsAndActions(grid, plan, lang) {
  const w = plan.ventilation_window, ww = plan.worst_window;
  const invActive = Boolean(plan.inversion?.hours?.length);
  grid.append(
    el('div', 'card grid-col-4', [el('h3', '', '🪟 Best time to open windows'), el('p', '', w ? `${w.start_hour}:00–${w.end_hour}:00` : 'None safe today'), el('small', 'help-text', w ? `Avg PM2.5: ${formatConcentration(w.mean_pm25)}` : 'Keep windows shut during severe smog')]),
    el('div', 'card grid-col-4', [el('h3', '', '⚠️ Worst time outside'), el('p', '', ww ? `${ww.start_hour}:00–${ww.end_hour}:00` : '18:00–21:00'), el('small', 'help-text', ww ? `Avg PM2.5: ${formatConcentration(ww.mean_pm25)}` : 'Evening peak traffic & inversion.')]),
    el('div', 'card grid-col-4', [el('h3', '', '🌡️ Inversion status'), el('p', '', invActive ? 'Active thermal trap' : 'Clear dispersion'), el('small', 'help-text', invActive ? 'Trapping ground-level smog until midday.' : 'Boundary layer dispersing pollutants.')]),
  );

  grid.appendChild(el('h3', 'grid-col-12', 'Your top actions'));
  (plan.ranked_interventions || []).slice(0, 3).forEach((item, i) => {
    const act = item.intervention || item;
    const costTxt = act.cost_inr_per_month > 0 ? `₹${act.cost_inr_per_month}/mo` : 'Free';
    const chips = el('div', 'chip-row', [
      el('span', 'badge', `#${i + 1}`),
      el('span', 'badge', costTxt),
      el('span', 'badge', `Effort ${act.effort}/5`),
    ]);
    const actCard = el('div', 'card grid-col-4', [chips, el('h4', '', act.title), el('p', '', item.why_this_rank)]);
    actCard.appendChild(el('details', 'impact-receipt', [
      el('summary', '', `🧾 ${t('impactReceipt', lang)}`),
      el('p', 'provenance-tag', `${t('assumptions', lang)}: ${act.provenance.text} [Confidence: ${act.provenance.confidence}]`),
    ]));
    grid.appendChild(actCard);
  });
}
