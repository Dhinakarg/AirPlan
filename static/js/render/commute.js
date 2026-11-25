/**
 * @fileoverview Accessible commute mode comparison table renderer.
 */

import { el } from '../dom.js';
import { labelFor, t } from '../i18n.js';

function exposureBandLabel(idx) {
  if (idx >= 110) return 'High';
  if (idx <= 75) return 'Lower';
  return 'Moderate';
}

/**
 * Render commute comparison table and assumptions details into target grid.
 *
 * @param {HTMLElement} grid - Target plan grid container.
 * @param {Record<string, any> | null | undefined} cmp - CommuteComparison payload.
 * @param {string} lang - Active UI language ('en' or 'hi').
 * @returns {void}
 */
export function renderCommuteTable(grid, cmp, lang) {
  if (!cmp || !Array.isArray(cmp.options) || !cmp.options.length) return;

  const card = el('div', 'card grid-col-12');
  const hdr = el('div', 'flex-between', [
    el('h3', '', `${t('commuteTitle', lang)} (${cmp.distance_km} km)`),
    el('span', 'badge', t('lowConfidence', lang)),
  ]);
  card.appendChild(hdr);

  const wrap = el('div', 'table-container');
  const tbl = el('table');
  tbl.appendChild(el('caption', '', t('commuteCaption', lang)));

  const thead = el('thead');
  const trH = el('tr');
  [
    t('commuteColMode', lang),
    t('commuteColExposure', lang),
    t('commuteColCost', lang),
    t('commuteColTime', lang),
    t('commuteColCo2', lang),
  ].forEach((col) => {
    const th = el('th', '', col);
    th.scope = 'col';
    trH.appendChild(th);
  });
  thead.appendChild(trH);
  tbl.appendChild(thead);

  const tbody = el('tbody');
  cmp.options.forEach((opt) => {
    const tr = el('tr');
    const modeLabel = labelFor('mode', opt.mode, lang);
    const expText = `${opt.exposure_index} (${exposureBandLabel(opt.exposure_index)})`;
    [
      modeLabel,
      expText,
      `₹${opt.cost_inr}`,
      `${opt.duration_minutes} min`,
      `${opt.co2_kg.toFixed(2)} kg`,
    ].forEach((val) => tr.appendChild(el('td', '', val)));
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
  wrap.appendChild(tbl);

  const det = el('details', 'impact-receipt', [
    el('summary', '', t('commuteAssumptions', lang)),
    el('p', '', cmp.assumptions),
  ]);

  card.append(wrap, det);
  grid.appendChild(card);
}
