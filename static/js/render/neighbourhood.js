/**
 * @fileoverview Screen 5: Neighbourhood pledge form and aggregated impact dashboard.
 */

import { announce, showError } from '../a11y.js';
import { fetchCommunitySummary, submitPledge } from '../api.js';
import { t } from '../i18n.js';
import { getState, setState } from '../state.js';

/**
 * Render Neighbourhood Screen.
 * @param {HTMLElement} container - Target container.
 * @returns {void}
 */
export function renderNeighbourhoodScreen(container) {
  container.replaceChildren();
  const s = getState();
  const lang = s.language;

  const title = document.createElement('h3');
  title.textContent = t('neighbourhoodTitle', lang);
  container.appendChild(title);

  // 1. Pledge Form
  const form = document.createElement('form');
  form.className = 'form-grid card';
  form.noValidate = true;

  // Area Code
  const areaRow = document.createElement('div');
  areaRow.className = 'form-group';
  const areaLbl = document.createElement('label');
  areaLbl.htmlFor = 'pledge-area-code';
  areaLbl.textContent = t('areaCode', lang);
  const areaIn = document.createElement('input');
  areaIn.type = 'text';
  areaIn.id = 'pledge-area-code';
  areaIn.value = 'DL-01';
  areaIn.pattern = '^[A-Z0-9-]{3,10}$';
  areaRow.appendChild(areaLbl);
  areaRow.appendChild(areaIn);
  form.appendChild(areaRow);

  // Action Select
  const actRow = document.createElement('div');
  actRow.className = 'form-group';
  const actLbl = document.createElement('label');
  actLbl.htmlFor = 'pledge-action-select';
  actLbl.textContent = t('pledgeAction', lang);
  const actSel = document.createElement('select');
  actSel.id = 'pledge-action-select';
  [
    { id: 'metro', label: 'Use Metro transit instead of car' },
    { id: 'carpool', label: 'Carpool with neighbours' },
    { id: 'no_waste_burning', label: 'Report and halt open waste burning' },
    { id: 'combine_errands', label: 'Combine local errand trips' },
  ].forEach((a) => {
    const opt = document.createElement('option');
    opt.value = a.id;
    opt.textContent = a.label;
    actSel.appendChild(opt);
  });
  actRow.appendChild(actLbl);
  actRow.appendChild(actSel);
  form.appendChild(actRow);

  // Count
  const countRow = document.createElement('div');
  countRow.className = 'form-group';
  const countLbl = document.createElement('label');
  countLbl.htmlFor = 'pledge-count-input';
  countLbl.textContent = t('pledgeCount', lang);
  const countIn = document.createElement('input');
  countIn.type = 'number';
  countIn.id = 'pledge-count-input';
  countIn.min = '1';
  countIn.max = '100';
  countIn.value = '5';
  countRow.appendChild(countLbl);
  countRow.appendChild(countIn);
  form.appendChild(countRow);

  // Submit button
  const submitBtn = document.createElement('button');
  submitBtn.type = 'submit';
  submitBtn.className = 'btn btn-primary';
  submitBtn.textContent = `🤝 ${t('submitPledge', lang)}`;
  form.appendChild(submitBtn);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    announce('Submitting community action pledge...');
    try {
      const code = areaIn.value.trim().toUpperCase();
      await submitPledge({
        area_code: code,
        action: actSel.value,
        count: Number(countIn.value) || 1,
      });
      const summary = await fetchCommunitySummary(code);
      setState({ communitySummary: summary });
      announce('Pledge recorded! Updated community dashboard metrics.');
    } catch (err) {
      showError(err instanceof Error ? err.message : 'Pledge failed');
    }
  });

  container.appendChild(form);

  // 2. Aggregate Dashboard (Separate Cards for CO2 and PM2.5)
  renderCommunityCards(container, s.communitySummary, lang);
}

function renderCommunityCards(container, summary, lang) {
  if (!summary) return;

  const dashboardWrap = document.createElement('div');
  dashboardWrap.className = 'community-dashboard';
  dashboardWrap.style.marginTop = '24px';

  // Card 1: CO2 Emissions and Trips Avoided Card
  const co2Card = document.createElement('div');
  co2Card.className = 'card';
  const co2Title = document.createElement('h3');
  co2Title.textContent = `🌱 ${t('co2Card', lang)}`;
  const co2P1 = document.createElement('p');
  co2P1.textContent = `Trips Avoided: ${summary.trips_avoided} • Distance Saved: ${summary.km_avoided} km`;
  const co2P2 = document.createElement('p');
  co2P2.style.fontWeight = '700';
  co2P2.style.color = '#15803d';
  co2P2.textContent = `CO₂ Reductions: ${summary.co2_kg_avoided.toFixed(1)} kg avoided across ${summary.participating_households} households.`;
  co2Card.appendChild(co2Title);
  co2Card.appendChild(co2P1);
  co2Card.appendChild(co2P2);
  dashboardWrap.appendChild(co2Card);

  // Card 2: PM2.5 Qualitative Note Card (Separate Card)
  const pm25Card = document.createElement('div');
  pm25Card.className = 'card callout-card';
  const pm25Title = document.createElement('h3');
  pm25Title.textContent = `💨 ${t('pm25Card', lang)}`;
  const pm25P = document.createElement('p');
  pm25P.textContent = summary.pm25_note;
  const pm25Prov = document.createElement('p');
  pm25Prov.className = 'provenance-tag';
  pm25Prov.textContent =
    'Scientific basis: Localized trip avoidance reduces neighborhood vehicular tailpipe emissions qualitatively.';
  pm25Card.appendChild(pm25Title);
  pm25Card.appendChild(pm25P);
  pm25Card.appendChild(pm25Prov);
  dashboardWrap.appendChild(pm25Card);

  container.appendChild(dashboardWrap);
}

