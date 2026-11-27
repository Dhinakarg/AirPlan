/**
 * @fileoverview Screen 5: Neighbourhood pledge form and aggregated impact dashboard.
 */

import { announce, showError } from '../a11y.js';
import { fetchCommunitySummary, submitPledge } from '../api.js';
import { el } from '../dom.js';
import { t } from '../i18n.js';
import { getState, setState } from '../state.js';

function renderCommunityCards(container, summary, lang) {
  if (!summary) return;
  const wrap = el('div', 'community-dashboard');
  wrap.style.marginTop = '24px';

  // Card 1: CO2 Emissions
  const co2Card = el('div', 'card');
  const co2P2 = el('p', '', `CO₂ Reductions: ${summary.co2_kg_avoided.toFixed(1)} kg avoided across ${summary.participating_households} households.`);
  co2P2.style.fontWeight = '700';
  co2P2.style.color = '#15803d';
  co2Card.append(
    el('h3', '', `🌱 ${t('co2Card', lang)}`),
    el('p', '', `Trips Avoided: ${summary.trips_avoided} • Distance Saved: ${summary.km_avoided} km`),
    co2P2,
  );
  wrap.appendChild(co2Card);

  // Card 2: PM2.5 Qualitative Note
  const pm25Card = el('div', 'card callout-card');
  pm25Card.append(
    el('h3', '', `💨 ${t('pm25Card', lang)}`),
    el('p', '', summary.pm25_note),
    el('p', 'provenance-tag', 'Scientific basis: Localized trip avoidance reduces neighborhood vehicular tailpipe emissions qualitatively.'),
  );
  wrap.appendChild(pm25Card);

  container.appendChild(wrap);
}

/**
 * Render Neighbourhood Screen.
 *
 * @param {HTMLElement} container - Target container element.
 * @returns {void}
 */
export function renderNeighbourhoodScreen(container) {
  container.replaceChildren();
  const s = getState(), lang = s.language;
  container.appendChild(el('h3', '', t('neighbourhoodTitle', lang)));

  const form = el('form', 'form-grid card');
  form.noValidate = true;

  // Area Code
  const areaIn = el('input');
  Object.assign(areaIn, { type: 'text', id: 'pledge-area-code', placeholder: 'e.g. DL-01', pattern: '^[A-Z0-9-]{3,10}$' });
  const areaLbl = el('label', '', t('areaCode', lang));
  areaLbl.htmlFor = areaIn.id;
  form.appendChild(el('div', 'form-group', [areaLbl, areaIn]));

  // Action Select
  const actSel = el('select');
  actSel.id = 'pledge-action-select';
  [
    { id: '', label: 'Select pledge action' },
    { id: 'metro', label: 'Use Metro transit instead of car' },
    { id: 'carpool', label: 'Carpool with neighbours' },
    { id: 'no_waste_burning', label: 'No waste burning' },
    { id: 'combine_errands', label: 'Combine local errand trips' },
  ].forEach((a, idx) => {
    const opt = el('option', '', a.label);
    opt.value = a.id;
    if (idx === 0) opt.selected = true;
    actSel.appendChild(opt);
  });
  const actLbl = el('label', '', t('pledgeAction', lang));
  actLbl.htmlFor = actSel.id;
  form.appendChild(el('div', 'form-group', [actLbl, actSel]));

  // Count
  const countIn = el('input');
  Object.assign(countIn, { type: 'number', id: 'pledge-count-input', min: '1', max: '100', placeholder: 'e.g. 5' });
  const countLbl = el('label', '', t('pledgeCount', lang));
  countLbl.htmlFor = countIn.id;
  form.appendChild(el('div', 'form-group', [countLbl, countIn]));

  // Submit button
  const submitBtn = el('button', 'btn btn-primary', `🤝 ${t('submitPledge', lang)}`);
  submitBtn.type = 'submit';
  form.appendChild(submitBtn);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const code = areaIn.value.trim().toUpperCase();
    const cnt = Number(countIn.value);
    if (!code || !actSel.value || !cnt) {
      showError('Please enter area code, pledge action, and days/trips.');
      return;
    }
    announce('Submitting community action pledge...');
    try {
      await submitPledge({
        area_code: code,
        action: actSel.value,
        count: cnt,
      });
      const summary = await fetchCommunitySummary(code);
      setState({ communitySummary: summary });
      announce('Pledge recorded! Updated community dashboard metrics.');
    } catch (err) {
      showError(err instanceof Error ? err.message : 'Pledge failed');
    }
  });

  container.appendChild(form);
  renderCommunityCards(container, s.communitySummary, lang);
}
