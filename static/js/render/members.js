/**
 * @fileoverview Renderer for personalized family member plans and actionable guidance.
 */

import { clearElement, el, makeBadge } from './common.js';

/**
 * Render individual member vulnerability cards into container.
 * @param {HTMLElement} container - Target container.
 * @param {Array<Object>} memberPlans - List of MemberExposurePlan objects.
 * @returns {void}
 */
export function renderMembers(container, memberPlans) {
  clearElement(container);

  if (!memberPlans || memberPlans.length === 0) {
    container.appendChild(el('p', { class: 'site-tagline' }, 'No family members enrolled.'));
    return;
  }

  memberPlans.forEach((plan) => {
    const isHighRisk = plan.vulnerability_score.value > 1.5;
    const vulnBadge = makeBadge(`${plan.vulnerability_score.value}x Risk`, isHighRisk ? 'high' : 'neutral');
    const redBadge = makeBadge(`-${plan.reduction_pct.value.toFixed(0)}%`, 'low');

    const header = el(
      'div',
      { style: 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;' },
      el('h4', { style: 'font-weight: 700; font-size: 1.1rem;' }, `${plan.member_name} (${plan.age_group})`),
      el('div', { style: 'display: flex; gap: 8px;' }, vulnBadge, redBadge)
    );

    const stats = el(
      'p',
      { class: 'site-tagline', style: 'margin-bottom: 12px; font-weight: 600;' },
      `Daily Inhaled Average: ${plan.baseline_24h_avg_pm25.value.toFixed(1)} → ${plan.mitigated_24h_avg_pm25.value.toFixed(1)} µg/m³`
    );

    const recsList = el('ul', { style: 'padding-left: 20px; font-size: 0.9rem;' });
    plan.key_recommendations.forEach((rec) => {
      recsList.appendChild(el('li', {}, rec));
    });

    const card = el(
      'div',
      {
        class: 'member-item',
        style: 'border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 16px; margin-bottom: 16px; background: var(--bg-surface);',
      },
      header,
      stats,
      recsList
    );

    container.appendChild(card);
  });
}

