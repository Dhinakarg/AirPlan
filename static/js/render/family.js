/**
 * @fileoverview Screen 1: Family and Household Setup view renderer.
 */

import { el } from '../dom.js';
import { labelFor, t } from '../i18n.js';
import { PRESET_CITIES, getState, setState } from '../state.js';
import { renderHouseholdSummary } from './summary.js';

function field(id, labelText, control, helpText) {
  const f = el('div', 'field'), lbl = el('label', '', labelText);
  lbl.htmlFor = control.id = id;
  f.append(lbl, control);
  if (helpText) {
    const s = el('small', { class: 'help-text', id: `${id}-help` }, helpText);
    control.setAttribute('aria-describedby', s.id);
    f.appendChild(s);
  }
  return f;
}

const opt = (val, text, sel = false) => Object.assign(document.createElement('option'), { value: val, textContent: text, selected: sel });

/**
 * Render Family setup screen into target container.
 * @param {HTMLElement} container - DOM container element.
 * @returns {void}
 */
export function renderFamilyScreen(container) {
  container.replaceChildren();
  const s = getState(), lang = s.language;
  const layout = el('div', 'step-layout'), mainCol = el('div', 'step-main');
  mainCol.append(el('h2', '', t('planningForTitle', lang)), el('p', 'member-counter', `${s.members.length} of 6 members`));

  // Card 1: Who lives here
  const c1 = el('div', 'card'), memList = el('div', 'member-list');
  c1.appendChild(el('h3', '', t('whoLivesHere', lang)));
  s.members.forEach((m, idx) => {
    const card = el('div', 'member-card'), info = el('div', 'member-info');
    const av = el('span', 'avatar-circle', (m.name || 'M').charAt(0).toUpperCase());
    av.setAttribute('aria-hidden', 'true');
    const det = el('div', 'member-details');
    det.append(el('span', 'member-name', m.name), el('span', 'member-sublabel', `${labelFor('ageGroup', m.age_group, lang)} · ${labelFor('sensitivity', m.sensitivity, lang)}`));
    info.append(av, det);
    card.appendChild(info);
    if (s.members.length > 1) {
      const rm = Object.assign(el('button', 'ghost', t('removeMember', lang)), { type: 'button' });
      rm.setAttribute('aria-label', `Remove ${m.name}`);
      rm.addEventListener('click', () => {
        const next = s.members.filter((_, i) => i !== idx);
        setState({ members: next, activeMemberIndex: 0 });
      });
      card.appendChild(rm);
    }
    memList.appendChild(card);
  });
  c1.appendChild(memList);

  if (s.members.length < 6) {
    const openBtn = Object.assign(el('button', 'btn btn-secondary', `+ ${t('addMember', lang)}`), { type: 'button', id: 'open-add-member-btn' });
    const openRow = el('div', 'actions'); openRow.appendChild(openBtn);
    const panel = el('div', 'add-member-panel');
    panel.hidden = true;
    panel.appendChild(el('h3', '', t('addMember', lang)));
    const nameIn = Object.assign(el('input'), { type: 'text', placeholder: 'e.g. Priyo' });
    const ageSel = el('select'), sensSel = el('select');
    ageSel.appendChild(Object.assign(opt('', 'Select age group', true), { disabled: true }));
    sensSel.appendChild(Object.assign(opt('', 'Select health needs', true), { disabled: true }));
    ['toddler', 'child', 'teen', 'adult', 'senior'].forEach((a) => ageSel.appendChild(opt(a, labelFor('ageGroup', a, lang))));
    ['none', 'asthma_or_heart', 'pregnant'].forEach((k) => sensSel.appendChild(opt(k, labelFor('sensitivity', k, lang))));
    const errEl = Object.assign(el('p', 'form-error', ''), { id: 'new-member-error' });
    errEl.setAttribute('role', 'alert');
    const saveBtn = Object.assign(el('button', 'btn primary btn-primary', 'Save Member'), { type: 'button' });
    const cancelBtn = Object.assign(el('button', 'btn btn-secondary', 'Cancel'), { type: 'button' });
    const toggleAddView = (open) => {
      panel.hidden = !open; memList.hidden = open; openRow.hidden = open;
      hbGrid.hidden = open; actions.hidden = open;
      if (open) nameIn.focus(); else errEl.textContent = '';
    };
    openBtn.addEventListener('click', () => toggleAddView(true));
    cancelBtn.addEventListener('click', () => toggleAddView(false));
    saveBtn.addEventListener('click', () => {
      const val = nameIn.value.trim();
      if (!val || !ageSel.value || !sensSel.value) {
        errEl.textContent = 'Please enter name, age group, and health needs.';
        (!val ? nameIn : !ageSel.value ? ageSel : sensSel).focus();
        return;
      }
      setState({ members: [...s.members, { name: val, age_group: ageSel.value, sensitivity: sensSel.value, routine: JSON.parse(JSON.stringify(s.members[0].routine)) }] });
    });
    const r1 = el('div', 'field-row'), r2 = el('div', 'field-row'), btnRow = el('div', 'actions');
    r1.append(field('new-member-name', t('memberName', lang), nameIn, 'Name or nickname'), field('new-member-age', t('ageGroup', lang), ageSel, 'Age category'));
    r2.appendChild(field('new-member-sens', t('sensitivity', lang), sensSel, 'Respiratory health needs'));
    btnRow.append(cancelBtn, saveBtn);
    panel.append(r1, r2, errEl, btnRow);
    c1.append(openRow, panel);
  }
  mainCol.appendChild(c1);

  // Two open cards ("Your home" & "Your budget") in a two-column desktop grid
  const hbGrid = el('div', 'grid-2col');
  const c2 = el('div', 'card'), leakSel = el('select'), citySel = el('select');
  c2.appendChild(el('h3', '', t('yourHome', lang)));
  leakSel.appendChild(opt('', 'Select home leakiness', !s.homeSelected));
  ['tight', 'average', 'leaky'].forEach((l) => leakSel.appendChild(opt(l, labelFor('leakiness', l, lang), Boolean(s.homeSelected && l === s.home.leakiness))));
  leakSel.addEventListener('change', (e) => { if (e.target.value) setState({ homeSelected: true, home: { ...s.home, leakiness: e.target.value } }); });
  citySel.appendChild(opt('', 'Select city', !s.citySelected));
  Object.entries(PRESET_CITIES).forEach(([k, c]) => citySel.appendChild(opt(k, `${c.name} (${c.lat}, ${c.lon})`, Boolean(s.citySelected && k === s.city))));
  citySel.addEventListener('change', (e) => { const d = PRESET_CITIES[e.target.value]; if (d) setState({ citySelected: true, city: e.target.value, latitude: d.lat, longitude: d.lon }); });
  const homeRow = el('div', 'field-row');
  homeRow.append(field('home-leakiness-select', t('draughtyQuestion', lang), leakSel, 'Affects outdoor smoke infiltration'), field('city-preset-select', t('cityPreset', lang), citySel, 'Forecast location for smog calculations'));

  const pF = el('div', 'field'), pLbl = el('label', '', ` ${t('purifier', lang)}`);
  const pChk = Object.assign(el('input'), { type: 'checkbox', id: 'home-purifier-chk', checked: s.home.purifier });
  pLbl.htmlFor = pChk.id;
  pChk.addEventListener('change', (e) => setState({ home: { ...s.home, purifier: e.target.checked } }));
  pLbl.prepend(pChk);
  const pHelp = Object.assign(el('small', 'help-text', 'Used in ventilation and indoor simulation logic.'), { id: 'home-purifier-help' });
  pChk.setAttribute('aria-describedby', pHelp.id);
  pF.append(pLbl, pHelp);
  c2.append(homeRow, pF);

  const c3 = el('div', 'card'), bF = el('div', 'field'), bRow = el('div', 'field-row');
  c3.appendChild(el('h3', '', t('yourBudget', lang)));
  const bLbl = Object.assign(el('label', '', s.budgetSelected ? `₹${s.budgetInr} per month` : 'Enter monthly budget (INR)'), { htmlFor: 'budget-slider', id: 'budget-amount-label' });
  const bRange = Object.assign(el('input'), { type: 'range', id: 'budget-slider', min: '0', max: '20000', step: '100', value: String(s.budgetInr) });
  const bNum = Object.assign(el('input'), { type: 'number', id: 'budget-number', min: '0', max: '100000', placeholder: 'e.g. 500', value: s.budgetSelected ? String(s.budgetInr) : '' });
  const bHelp = Object.assign(el('small', 'help-text', t('budgetHelp', lang)), { id: 'budget-change-help' });
  bRange.setAttribute('aria-describedby', bHelp.id);
  bNum.setAttribute('aria-describedby', bHelp.id);
  const syncB = (raw, fromNum = false) => {
    const v = Math.max(0, Math.min(100000, Number(raw) || 0));
    bRange.value = String(Math.min(20000, v)); if (!fromNum) bNum.value = String(v);
    bLbl.textContent = `₹${v} per month`;
    const sumEl = document.getElementById('summary-budget-val'); if (sumEl) sumEl.textContent = `₹${v} / mo`;
    setState({ budgetSelected: true, budgetInr: v }, true);
  };
  bRange.addEventListener('input', (e) => syncB(e.target.value, false));
  bNum.addEventListener('input', (e) => syncB(e.target.value, true));
  bRow.append(bRange, bNum); bF.append(bLbl, bRow, bHelp); c3.append(bF);
  hbGrid.append(c2, c3); mainCol.appendChild(hbGrid);
  const actions = el('div', 'actions');
  actions.appendChild(Object.assign(el('button', 'btn primary btn-primary', t('nextYourDay', lang)), { type: 'button', id: 'next-to-ledger-btn' }));
  mainCol.append(actions); layout.append(mainCol, renderHouseholdSummary(s, lang)); container.appendChild(layout);
}
