/**
 * @fileoverview Screen 4: Home Detective indoor source questionnaire & findings.
 */

import { announce, showError } from '../a11y.js';
import { analyzeHome } from '../api.js';
import { el } from '../dom.js';
import { t } from '../i18n.js';
import { getState, setState } from '../state.js';

function makeSelect(id, label, options) {
  const sel = el('select');
  sel.id = id;
  options.forEach((o) => {
    const opt = el('option', '', o);
    opt.value = o;
    sel.appendChild(opt);
  });
  const lbl = el('label', '', label);
  lbl.htmlFor = id;
  return [el('div', 'form-group', [lbl, sel]), sel];
}

function renderFindings(findings, lang) {
  const card = el('div', 'card');
  card.style.marginTop = '24px';
  card.appendChild(el('h3', '', 'Identified Sources & Practical Fixes'));

  findings.forEach((f) => {
    const item = el('div', 'source-item card');
    const badgeClass = f.status === 'measured' ? 'badge badge-high' : 'badge badge-medium';
    const badgeText = f.status === 'measured' ? `🔬 ${t('measured', lang)}` : `⚠️ ${t('suspected', lang)}`;
    const hdr = el('div', 'flex-between', [el('strong', '', f.source), el('span', badgeClass, badgeText)]);
    const ev = el('p', 'meta-text', `Evidence: ${f.evidence} (Likelihood: ${(f.likelihood * 100).toFixed(0)}%)`);
    item.append(hdr, ev);

    if (f.fixes?.length) {
      const ul = el('ul');
      f.fixes.forEach((fix) => ul.appendChild(el('li', '', fix)));
      item.appendChild(ul);
    }
    card.appendChild(item);
  });
  return card;
}

/**
 * Render Home Detective screen into container.
 * @param {HTMLElement} container - Target container.
 * @returns {void}
 */
export function renderDetectiveScreen(container) {
  container.replaceChildren();
  const s = getState(), lang = s.language;
  container.appendChild(el('h3', '', t('detectiveTitle', lang)));

  const form = el('form', 'form-grid');
  form.noValidate = true;

  const [fuelRow, fuelSel] = makeSelect('detective-fuel', t('cookingFuel', lang), ['lpg', 'biomass', 'kerosene', 'induction', 'electric_coil']);
  const [exhRow, exhSel] = makeSelect('detective-exhaust', t('kitchenExhaust', lang), ['none', 'internal', 'vented']);
  const [swRow, sweepSel] = makeSelect('detective-sweeping', t('sweeping', lang), ['dry', 'wet']);
  form.append(fuelRow, exhRow, swRow);

  const chkGroup = el('div', 'form-group');
  const chkItems = [
    { id: 'det-incense', label: t('incense', lang), default: true },
    { id: 'det-coil', label: t('mosquitoCoil', lang), default: true },
    { id: 'det-smokers', label: t('smokers', lang), default: false },
    { id: 'det-pets', label: t('pets', lang), default: false },
  ];
  chkItems.forEach((it) => {
    const chk = el('input');
    chk.type = 'checkbox';
    chk.id = it.id;
    chk.checked = it.default;
    const lbl = el('label', 'checkbox-label');
    lbl.htmlFor = it.id;
    lbl.append(chk, el('span', '', it.label));
    chkGroup.appendChild(lbl);
  });
  form.appendChild(chkGroup);

  const readIn = el('input');
  readIn.type = 'number';
  readIn.id = 'detective-reading';
  readIn.min = '0';
  readIn.step = '1';
  readIn.placeholder = 'e.g. 140';
  const readLbl = el('label', '', t('indoorReading', lang));
  readLbl.htmlFor = 'detective-reading';
  form.appendChild(el('div', 'form-group', [readLbl, readIn]));

  const submitBtn = el('button', 'btn btn-primary', `🔍 ${t('analyzeSources', lang)}`);
  submitBtn.type = 'submit';
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
    container.appendChild(renderFindings(s.detectiveFindings, lang));
  }
}
