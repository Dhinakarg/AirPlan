/**
 * @fileoverview Renderer for identified indoor pollution sources.
 */

import { clearElement, el, makeBadge } from './common.js';

/**
 * Render indoor sources findings list into container.
 * @param {HTMLElement} container - Target container.
 * @param {Array<Object>} sources - Identified indoor source findings.
 * @returns {void}
 */
export function renderSources(container, sources) {
  clearElement(container);

  if (!sources || sources.length === 0) {
    const emptyNotice = el(
      'p',
      { class: 'site-tagline' },
      'No elevated internal combustion or smoldering sources detected in your household.'
    );
    container.appendChild(emptyNotice);
    return;
  }

  const list = el('div', { class: 'sources-grid' });

  sources.forEach((source) => {
    const badge = makeBadge(source.severity.toUpperCase(), source.severity);
    const titleRow = el(
      'div',
      { style: 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;' },
      el('h4', { style: 'font-weight: 700; font-size: 1.05rem;' }, source.name),
      badge
    );

    const emissionText = `Emission Rate: ~${source.emission_rate_mg_h.value} mg/h (Hours: ${source.peak_hours.join(', ') || 'Continuous'})`;
    const rateEl = el('p', { class: 'site-tagline', style: 'font-weight: 600; margin-bottom: 6px;' }, emissionText);
    const descEl = el('p', { style: 'margin-bottom: 8px;' }, source.description);
    const hintEl = el(
      'div',
      { style: 'padding: 8px 12px; background: var(--bg-surface-elevated); border-radius: var(--radius-sm); font-size: 0.85rem;' },
      el('strong', {}, 'Fix: '),
      source.mitigation_hint
    );

    const card = el(
      'div',
      {
        class: 'source-item',
        style: 'border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 16px; margin-bottom: 12px;',
      },
      titleRow,
      rateEl,
      descEl,
      hintEl
    );

    list.appendChild(card);
  });

  container.appendChild(list);
}

