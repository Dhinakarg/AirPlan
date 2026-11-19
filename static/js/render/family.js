/**
 * @fileoverview Screen 1: Family and Household Setup view renderer.
 */

import { el } from '../dom.js';
import { labelFor, t } from '../i18n.js';
import { PRESET_CITIES, getState, setState } from '../state.js';

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

function renderHouseholdSummary(s, lang) {
  const aside = el('aside', 'step-aside'), sumCard = el('div', 'card summary-card'), dl = el('dl', 'summary-list');
  sumCard.appendChild(el('h3', '', t('yourHousehold', lang)));
  [
    ['Members', `${s.members.length} of 6`],
    ['Home type', labelFor('leakiness', s.home.leakiness, lang)],
    ['City', PRESET_CITIES[s.city]?.name.split(' (')[0] || s.city],
    ['Budget', `₹${s.budgetInr} / mo`],
  ].forEach(([dt, dd]) => {
    const it = el('div', 'summary-item');
    it.append(el('dt', '', dt), el('dd', '', dd));
    dl.appendChild(it);
  });
  sumCard.append(dl, el('p', 'summary-hint', t('hintNextRoutine', lang)));
  aside.appendChild(sumCard);
  return aside;
}

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
      const rm = el('button', 'ghost', t('removeMember', lang));
      rm.type = 'button';
      rm.setAttribute('aria-label', `Remove ${m.name}`);
      rm.addEventListener('click', () => {
        const next = [...s.members];
        next.splice(idx, 1);
        setState({ members: next, activeMemberIndex: 0 });
      });
      card.appendChild(rm);
    }
    memList.appendChild(card);
  });
  c1.appendChild(memList);

  if (s.members.length < 6) {
    const nameIn = Object.assign(el('input'), { type: 'text', placeholder: 'e.g. Priyo' });
    const ageSel = el('select'), sensSel = el('select');
    ['toddler', 'child', 'teen', 'adult', 'senior'].forEach((a) => ageSel.appendChild(opt(a, labelFor('ageGroup', a, lang), a === 'adult')));
    ['none', 'asthma_or_heart', 'pregnant'].forEach((k) => sensSel.appendChild(opt(k, labelFor('sensitivity', k, lang))));
    const addBtn = Object.assign(el('button', 'btn btn-secondary', `+ ${t('addMember', lang)}`), { type: 'button' });
    addBtn.addEventListener('click', () => {
      const val = nameIn.value.trim() || `Member ${s.members.length + 1}`;
      setState({ members: [...s.members, { name: val, age_group: ageSel.value, sensitivity: sensSel.value, routine: JSON.parse(JSON.stringify(s.members[0].routine)) }] });
    });
    const r1 = el('div', 'field-row'), r2 = el('div', 'field-row'), wrap = el('div', 'field');
    r1.append(field('new-member-name', t('memberName', lang), nameIn, 'Name or nickname'), field('new-member-age', t('ageGroup', lang), ageSel, 'Age category'));
    wrap.appendChild(addBtn);
    r2.append(field('new-member-sens', t('sensitivity', lang), sensSel, 'Respiratory health needs'), wrap);
    c1.append(r1, r2);
  }
  mainCol.appendChild(c1);

  // Card 2: Your home
  const c2 = el('div', 'card'), leakSel = el('select'), citySel = el('select');
  c2.appendChild(el('h3', '', t('yourHome', lang)));
  ['tight', 'average', 'leaky'].forEach((l) => leakSel.appendChild(opt(l, labelFor('leakiness', l, lang), l === s.home.leakiness)));
  leakSel.addEventListener('change', (e) => setState({ home: { ...s.home, leakiness: e.target.value } }));
  Object.entries(PRESET_CITIES).forEach(([k, c]) => citySel.appendChild(opt(k, `${c.name} (${c.lat}, ${c.lon})`, k === s.city)));
  citySel.addEventListener('change', (e) => {
    const d = PRESET_CITIES[e.target.value];
    if (d) setState({ city: e.target.value, latitude: d.lat, longitude: d.lon });
  });
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
  mainCol.appendChild(c2);

  // Card 3: Your budget
  const c3 = el('div', 'card'), bF = el('div', 'field'), bRow = el('div', 'field-row');
  c3.appendChild(el('h3', '', t('yourBudget', lang)));
  const bLbl = Object.assign(el('label', '', `₹${s.budgetInr} per month`), { htmlFor: 'budget-slider', id: 'budget-amount-label' });
  const bRange = Object.assign(el('input'), { type: 'range', id: 'budget-slider', min: '0', max: '20000', step: '100', value: String(s.budgetInr) });
  const bNum = Object.assign(el('input'), { type: 'number', id: 'budget-number', min: '0', max: '100000', value: String(s.budgetInr) });
  const bHelp = Object.assign(el('small', 'help-text', t('budgetHelp', lang)), { id: 'budget-change-help' });
  bRange.setAttribute('aria-describedby', bHelp.id);
  bNum.setAttribute('aria-describedby', bHelp.id);
  const syncB = (v) => {
    bRange.value = String(Math.min(20000, v));
    bNum.value = String(v);
    bLbl.textContent = `₹${v} per month`;
    setState({ budgetInr: v });
  };
  bRange.addEventListener('input', (e) => syncB(Number(e.target.value)));
  bNum.addEventListener('input', (e) => syncB(Number(e.target.value) || 0));
  bRow.append(bRange, bNum);
  bF.append(bLbl, bRow, bHelp);
  c3.append(bF);
  mainCol.appendChild(c3);

  // Actions row
  const actions = el('div', 'actions');
  actions.appendChild(Object.assign(el('button', 'btn primary btn-primary', t('nextYourDay', lang)), { type: 'button', id: 'next-to-ledger-btn' }));
  mainCol.append(actions);

  layout.append(mainCol, renderHouseholdSummary(s, lang));
  container.appendChild(layout);
}
