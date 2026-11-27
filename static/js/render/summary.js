/**
 * @fileoverview Household summary sidebar card renderer for Step 1.
 */

import { el } from '../dom.js';
import { labelFor, t } from '../i18n.js';
import { PRESET_CITIES } from '../state.js';

/**
 * Render the sticky household summary sidebar card.
 * @param {Record<string, any>} s - Application state.
 * @param {string} lang - Active UI language.
 * @returns {HTMLElement} Summary aside element.
 */
export function renderHouseholdSummary(s, lang) {
  const aside = el('aside', 'step-aside');
  const sumCard = el('div', 'card summary-card');
  const dl = el('dl', 'summary-list');
  sumCard.appendChild(el('h3', '', t('yourHousehold', lang)));
  [
    ['Members', `${s.members.length} of 6`],
    ['Home type', labelFor('leakiness', s.home.leakiness, lang)],
    ['City', PRESET_CITIES[s.city]?.name.split(' (')[0] || s.city],
    ['Budget', `₹${s.budgetInr} / mo`],
  ].forEach(([dt, dd]) => {
    const it = el('div', 'summary-item');
    const ddEl = el('dd', '', dd);
    if (dt === 'Budget') ddEl.id = 'summary-budget-val';
    it.append(el('dt', '', dt), ddEl);
    dl.appendChild(it);
  });
  sumCard.appendChild(dl);
  aside.appendChild(sumCard);
  return aside;
}

