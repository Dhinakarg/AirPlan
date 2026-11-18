/**
 * @fileoverview Renderer for ranked clean air interventions with interactive checkboxes.
 */

import { clearElement, el, makeBadge } from './common.js';

/**
 * Render prioritized interventions with interactive toggles.
 * @param {HTMLElement} container - DOM container.
 * @param {Array<Object>} interventions - Ranked InterventionOption list.
 * @param {function(string, boolean): void} onToggle - Callback when intervention is checked/unchecked.
 * @returns {void}
 */
export function renderInterventions(container, interventions, onToggle) {
  clearElement(container);

  if (!interventions || interventions.length === 0) {
    container.appendChild(el('p', { class: 'site-tagline' }, 'No intervention strategies available.'));
    return;
  }

  interventions.forEach((item) => {
    const chk = el('input', {
      type: 'checkbox',
      id: `it-${item.id}`,
      'aria-label': item.name,
      ...(item.is_active ? { checked: 'true' } : {}),
      onchange: (e) => {
        onToggle(item.id, e.target.checked);
      },
    });

    const costBadge = makeBadge(`₹${item.estimated_cost_inr.value.toFixed(0)}`, 'neutral');
    const redBadge = makeBadge(`-${item.estimated_reduction_pct.value.toFixed(0)}% Smog`, 'low');
    const diffBadge = makeBadge(item.difficulty.toUpperCase(), 'neutral');

    const header = el(
      'div',
      { style: 'display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;' },
      el(
        'label',
        { for: `it-${item.id}`, class: 'checkbox-label', style: 'font-weight: 700; font-size: 1rem;' },
        chk,
        item.name
      ),
      el('div', { style: 'display: flex; gap: 6px;' }, redBadge, costBadge, diffBadge)
    );

    const desc = el('p', { style: 'margin: 8px 0; font-size: 0.9rem;' }, item.description);

    const stepsList = el('ul', { style: 'padding-left: 20px; font-size: 0.85rem; color: var(--text-secondary);' });
    item.practical_steps.forEach((step) => {
      stepsList.appendChild(el('li', {}, step));
    });

    const card = el(
      'div',
      {
        class: 'intervention-item',
        style: `border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 16px; margin-bottom: 12px; background: ${item.is_active ? 'var(--bg-surface-elevated)' : 'var(--bg-surface)'};`,
      },
      header,
      desc,
      stepsList
    );

    container.appendChild(card);
  });
}

