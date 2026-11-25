/**
 * @fileoverview 24-hour particulate exposure SVG chart and accessible data table.
 */

import { el } from '../dom.js';
import { formatConcentration, getAqiCategory } from '../i18n.js';

/**
 * Render 24-hour timeline SVG chart and paired data table into section.
 *
 * @param {HTMLElement} sec - Target card element.
 * @param {Record<string, any> | undefined} memberExposure - Member DayExposure object.
 * @returns {void}
 */
export function renderTimelineInto(sec, memberExposure) {
  if (!memberExposure?.hours) return;
  sec.appendChild(el('h3', '', '24-Hour Particulate Exposure Timeline'));

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 480 160');
  svg.setAttribute('class', 'chart-svg');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', 'Hourly particulate exposure graph across 24 hours');

  const maxVal = Math.max(...memberExposure.hours.map((h) => h.pm25_ug_m3), 300);
  let pathD = '';
  memberExposure.hours.forEach((h, i) => {
    const x = i * 20 + 10;
    const y = 140 - (h.pm25_ug_m3 / maxVal) * 120;
    pathD += (i === 0 ? 'M' : 'L') + `${x},${y}`;
  });
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', pathD);
  path.setAttribute('fill', 'none');
  path.setAttribute('stroke', '#0b7a75');
  path.setAttribute('stroke-width', '3');
  svg.appendChild(path);
  sec.appendChild(svg);

  const wrap = el('div', 'table-container');
  const tbl = el('table');
  tbl.appendChild(el('caption', '', 'Hour-by-hour particulate exposure concentrations and AQI classifications'));
  const thead = el('thead');
  const trH = el('tr');
  ['Hour', 'PM2.5 Conc', 'Inhaled Dose', 'AQI Category'].forEach((h) => {
    const th = el('th', '', h);
    th.scope = 'col';
    trH.appendChild(th);
  });
  thead.appendChild(trH);
  tbl.appendChild(thead);

  const tbody = el('tbody');
  memberExposure.hours.forEach((h) => {
    const tr = el('tr');
    const aqi = getAqiCategory(h.pm25_ug_m3);
    const dose = h.inhaled_dose_ug ?? h.dose_ug ?? 0;
    [`${h.hour}:00`, formatConcentration(h.pm25_ug_m3), `${dose.toFixed(1)} µg`, `${aqi.icon} ${aqi.label} ${aqi.pattern}`].forEach((val) => {
      tr.appendChild(el('td', '', val));
    });
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
  wrap.appendChild(tbl);
  sec.appendChild(wrap);
}
