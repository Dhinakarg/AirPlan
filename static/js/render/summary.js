/**
 * @fileoverview Renderer for executive KPIs, summary banner, and provenance statements.
 */

import { clearElement, el } from './common.js';

/**
 * Render KPI metrics, plain language summary, and scientific assumptions.
 * @param {Object} plan - Computed CleanAirPlan domain object.
 * @param {boolean} plainLanguageMode - Whether simplified plain language is active.
 * @returns {void}
 */
export function renderSummaryCards(plan, plainLanguageMode = false) {
  const summaryBox = document.getElementById('summary-text');
  const kpiRed = document.getElementById('kpi-reduction');
  const kpiIndoor = document.getElementById('kpi-indoor-avg');
  const kpiStatus = document.getElementById('kpi-peak-status');

  if (!plan) {
    return;
  }

  if (summaryBox) {
    clearElement(summaryBox);
    const summaryMsg = plainLanguageMode
      ? `Simple View: Your home air will be ${plan.overall_household_reduction_pct.value.toFixed(0)}% cleaner today by sealing windows in the morning and running the DIY filter.`
      : plan.plain_language_summary;
    summaryBox.appendChild(el('span', {}, summaryMsg));
  }

  if (kpiRed) {
    kpiRed.textContent = `-${plan.overall_household_reduction_pct.value.toFixed(1)}%`;
  }

  if (kpiIndoor && plan.indoor_mitigated_24h && plan.indoor_mitigated_24h.length > 0) {
    const avg =
      plan.indoor_mitigated_24h.reduce((acc, p) => acc + p.value, 0) / plan.indoor_mitigated_24h.length;
    kpiIndoor.textContent = avg.toFixed(1);
  }

  if (kpiStatus) {
    const exceedsWho = plan.member_plans.some((m) => m.who_limit_exceeded);
    kpiStatus.textContent = exceedsWho ? 'Severe Smog' : 'Moderate';
    kpiStatus.style.color = exceedsWho ? 'var(--color-danger)' : 'var(--color-success)';
  }
}

