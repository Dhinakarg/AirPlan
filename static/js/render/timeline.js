/**
 * @fileoverview Renderer for 24-hour hour-by-hour exposure comparison chart (SVG) and accessible table.
 */

import { clearElement, el } from './common.js';

/**
 * Generate an accessible SVG visualization representing diurnal PM2.5 trajectories.
 * @param {number[]} outdoor - Outdoor hourly PM2.5 concentrations.
 * @param {number[]} baseline - Unmitigated indoor concentrations.
 * @param {number[]} mitigated - Mitigated indoor concentrations.
 * @returns {SVGElement} Accessible SVG DOM element.
 */
function buildExposureSvg(outdoor, baseline, mitigated) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 720 220');
  svg.setAttribute('class', 'chart-svg');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', '24-hour PM2.5 concentration comparison graph');

  const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
  title.textContent = '24-Hour Smog Concentration Curve';
  svg.appendChild(title);

  const maxVal = Math.max(500, ...outdoor, ...baseline, ...mitigated);
  const scaleX = (h) => 40 + h * 28;
  const scaleY = (v) => 190 - (v / maxVal) * 160;

  const makePath = (vals, stroke, dash, width) => {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const d = vals.map((val, idx) => `${idx === 0 ? 'M' : 'L'} ${scaleX(idx)} ${scaleY(val)}`).join(' ');
    path.setAttribute('d', d);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', stroke);
    path.setAttribute('stroke-width', width);
    if (dash) path.setAttribute('stroke-dasharray', dash);
    return path;
  };

  svg.appendChild(makePath(outdoor, '#b91c1c', '6,4', '2.5')); // Outdoor: Red dashed
  svg.appendChild(makePath(baseline, '#b45309', '3,3', '2.5')); // Baseline: Amber dotted
  svg.appendChild(makePath(mitigated, '#15803d', '', '3.5')); // Mitigated: Green solid

  return svg;
}

/**
 * Render exposure chart and accessible equivalent data table.
 * @param {HTMLElement} chartContainer - Container for SVG chart.
 * @param {HTMLElement} tableBody - Table body tbody container.
 * @param {Object} plan - CleanAirPlan domain object.
 * @returns {void}
 */
export function renderTimeline(chartContainer, tableBody, plan) {
  clearElement(chartContainer);
  clearElement(tableBody);

  if (!plan || !plan.indoor_mitigated_24h) {
    return;
  }

  const outdoorVals = plan.outdoor_forecast_24h.map((p) => p.value);
  const baseVals = plan.indoor_baseline_24h.map((p) => p.value);
  const mitVals = plan.indoor_mitigated_24h.map((p) => p.value);

  const svgChart = buildExposureSvg(outdoorVals, baseVals, mitVals);
  chartContainer.appendChild(svgChart);

  // Render Accessible Equivalent Table
  const sampleMember = plan.member_plans[0];
  for (let h = 0; h < 24; h++) {
    const hourLabel = `${String(h).padStart(2, '0')}:00`;
    const actionText = sampleMember ? sampleMember.hourly_timeline[h].recommended_action : 'Seal windows';

    const row = el(
      'tr',
      {},
      el('th', { scope: 'row' }, hourLabel),
      el('td', {}, outdoorVals[h].toFixed(1)),
      el('td', { style: 'font-weight: 700;' }, mitVals[h].toFixed(1)),
      el('td', {}, actionText)
    );
    tableBody.appendChild(row);
  }
}

