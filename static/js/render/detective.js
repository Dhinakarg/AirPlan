/**
 * @fileoverview Screen 4: Home Detective indoor source questionnaire & findings.
 */

import { announce, showError } from '../a11y.js';
import { analyzeHome } from '../api.js';
import { t } from '../i18n.js';
import { getState, setState } from '../state.js';

function makeSelect(id, label, options) {
  const row = document.createElement('div');
  row.className = 'form-group';
  const lbl = document.createElement('label');
  lbl.htmlFor = id;
  lbl.textContent = label;
  const sel = document.createElement('select');
  sel.id = id;
  options.forEach((o) => {
    const opt = document.createElement('option');
    opt.value = opt.textContent = o;
    sel.appendChild(opt);
  });
  row.appendChild(lbl);
  row.appendChild(sel);
  return [row, sel];
}

/**
 * Render Home Detective screen.
 * @param {HTMLElement} container - Target container.
 * @returns {void}
 */
export function renderDetectiveScreen(container) {
  container.replaceChildren();
  const s = getState();
  const lang = s.language;

  const title = document.createElement('h3');
  title.textContent = t('detectiveTitle', lang);
  container.appendChild(title);

  const form = document.createElement('form');
  form.className = 'form-grid';
  form.noValidate = true;

  const [fuelRow, fuelSel] = makeSelect('detective-fuel', t('cookingFuel', lang), [
    'lpg',
    'biomass',
    'kerosene',
    'induction',
    'electric_coil',
  ]);
  const [exhRow, exhSel] = makeSelect('detective-exhaust', t('kitchenExhaust', lang), [
    'none',
    'internal',
    'vented',
  ]);
  const [swRow, sweepSel] = makeSelect('detective-sweeping', t('sweeping', lang), ['dry', 'wet']);
  form.appendChild(fuelRow);
  form.appendChild(exhRow);
  form.appendChild(swRow);

  // Checkboxes
  const chkGroup = document.createElement('div');
  chkGroup.className = 'form-group';
  [
    { id: 'det-incense', label: t('incense', lang), default: true },
    { id: 'det-coil', label: t('mosquitoCoil', lang), default: true },
    { id: 'det-smokers', label: t('smokers', lang), default: false },
    { id: 'det-pets', label: t('pets', lang), default: false },
  ].forEach((it) => {
    const lbl = document.createElement('label');
    lbl.className = 'checkbox-label';
    lbl.htmlFor = it.id;
    const chk = document.createElement('input');
    chk.type = 'checkbox';
    chk.id = it.id;
    chk.checked = it.default;
    const span = document.createElement('span');
    span.textContent = it.label;
    lbl.appendChild(chk);
    lbl.appendChild(span);
    chkGroup.appendChild(lbl);
  });
  form.appendChild(chkGroup);

  // Optional indoor reading
  const readRow = document.createElement('div');
  readRow.className = 'form-group';
  const readLbl = document.createElement('label');
  readLbl.htmlFor = 'detective-reading';
  readLbl.textContent = t('indoorReading', lang);
  const readIn = document.createElement('input');
  readIn.type = 'number';
  readIn.id = 'detective-reading';
  readIn.min = '0';
  readIn.step = '1';
  readIn.placeholder = 'e.g. 140';
  readRow.appendChild(readLbl);
  readRow.appendChild(readIn);
  form.appendChild(readRow);

  const submitBtn = document.createElement('button');
  submitBtn.type = 'submit';
  submitBtn.className = 'btn btn-primary';
  submitBtn.textContent = `🔍 ${t('analyzeSources', lang)}`;
  form.appendChild(submitBtn);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    announce('Diagnosing indoor pollution sources...');
    try {
      const readVal = readIn.value ? Number(readIn.value) : null;
      const res = await analyzeHome({
        cooking_fuel: fuelSel.value,
        kitchen_exhaust: exhSel.value,
        incense: document.getElementById('det-incense')?.checked || false,
        mosquito_coil: document.getElementById('det-coil')?.checked || false,
        smokers: document.getElementById('det-smokers')?.checked || false,
        pets: document.getElementById('det-pets')?.checked || false,
        sweeping: sweepSel.value,
        indoor_pm25_reading: readVal,
      });
      setState({ detectiveFindings: res.findings });
      announce(`Detected ${res.findings.length} indoor factors.`);
    } catch (err) {
      showError(err instanceof Error ? err.message : 'Diagnosis failed');
    }
  });

  container.appendChild(form);

  if (s.detectiveFindings?.length) {
    const card = document.createElement('div');
    card.className = 'card';
    card.style.marginTop = '24px';
    const fTitle = document.createElement('h3');
    fTitle.textContent = 'Identified Sources & Practical Fixes';
    card.appendChild(fTitle);

    s.detectiveFindings.forEach((f) => {
      const item = document.createElement('div');
      item.className = 'source-item card';
      const hdr = document.createElement('div');
      hdr.className = 'flex-between';
      const name = document.createElement('strong');
      name.textContent = f.source;
      const badge = document.createElement('span');
      badge.className = f.status === 'measured' ? 'badge badge-high' : 'badge badge-medium';
      badge.textContent =
        f.status === 'measured' ? `🔬 ${t('measured', lang)}` : `⚠️ ${t('suspected', lang)}`;
      hdr.appendChild(name);
      hdr.appendChild(badge);
      item.appendChild(hdr);

      const ev = document.createElement('p');
      ev.className = 'meta-text';
      ev.textContent = `Evidence: ${f.evidence} (Likelihood: ${(f.likelihood * 100).toFixed(0)}%)`;
      item.appendChild(ev);

      if (f.fixes?.length) {
        const ul = document.createElement('ul');
        f.fixes.forEach((fix) => {
          const li = document.createElement('li');
          li.textContent = fix;
          ul.appendChild(li);
        });
        item.appendChild(ul);
      }
      card.appendChild(item);
    });
    container.appendChild(card);
  }
}
