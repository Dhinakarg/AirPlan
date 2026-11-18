/**
 * @fileoverview Screen 1: Family and Household Setup view renderer.
 */

import { labelFor, t } from '../i18n.js';
import { PRESET_CITIES, getState, setState } from '../state.js';

function el(tag, cls = '', text = '') {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
}

function field(id, labelText, control, helpText) {
  const f = el('div', 'field');
  const lbl = el('label', '', labelText);
  lbl.htmlFor = id;
  control.id = id;
  f.append(lbl, control);
  if (helpText) {
    const s = el('small', 'help-text', helpText);
    s.id = `${id}-help`;
    control.setAttribute('aria-describedby', s.id);
    f.appendChild(s);
  }
  return f;
}

function opt(val, text, selected = false) {
  const o = document.createElement('option');
  o.value = val;
  o.textContent = text;
  if (selected) o.selected = true;
  return o;
}

export function renderFamilyScreen(container) {
  container.replaceChildren();
  const s = getState();
  const lang = s.language;

  const title = el('h2', '', t('planningForTitle', lang));
  const counter = el('p', 'member-counter', `${s.members.length} of 6 members`);
  container.append(title, counter);

  // Card 1: Who lives here
  const c1 = el('div', 'card');
  c1.appendChild(el('h3', '', t('whoLivesHere', lang)));
  const memList = el('div', 'member-list');

  s.members.forEach((m, idx) => {
    const card = el('div', 'member-card');
    const info = el('div', 'member-info');
    const av = el('span', 'avatar-circle', (m.name || 'M').charAt(0).toUpperCase());
    av.setAttribute('aria-hidden', 'true');

    const det = el('div', 'member-details');
    const sub = el('span', 'member-sublabel', `${m.name} · ${labelFor('ageGroup', m.age_group, lang)} · ${labelFor('sensitivity', m.sensitivity, lang)}`);
    det.append(el('span', 'member-name', m.name), sub);
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
    const nameIn = el('input');
    nameIn.type = 'text';
    nameIn.placeholder = 'e.g. Priyo';

    const ageSel = el('select');
    ['toddler', 'child', 'teen', 'adult', 'senior'].forEach((a) => ageSel.appendChild(opt(a, labelFor('ageGroup', a, lang), a === 'adult')));

    const sensSel = el('select');
    ['none', 'asthma_or_heart', 'pregnant'].forEach((k) => sensSel.appendChild(opt(k, labelFor('sensitivity', k, lang))));

    const addBtn = el('button', 'btn btn-secondary', `+ ${t('addMember', lang)}`);
    addBtn.type = 'button';
    addBtn.addEventListener('click', () => {
      const val = nameIn.value.trim() || `Member ${s.members.length + 1}`;
      setState({
        members: [...s.members, { name: val, age_group: ageSel.value, sensitivity: sensSel.value, routine: JSON.parse(JSON.stringify(s.members[0].routine)) }],
      });
    });

    const r1 = el('div', 'field-row');
    r1.append(field('new-member-name', t('memberName', lang), nameIn, 'Name or nickname'), field('new-member-age', t('ageGroup', lang), ageSel, 'Age category'));

    const r2 = el('div', 'field-row');
    const wrap = el('div', 'field');
    wrap.appendChild(addBtn);
    r2.append(field('new-member-sens', t('sensitivity', lang), sensSel, 'Respiratory sensitivity'), wrap);
    c1.append(r1, r2);
  }
  container.appendChild(c1);

  // Card 2: Your home
  const c2 = el('div', 'card');
  c2.appendChild(el('h3', '', t('yourHome', lang)));

  const leakSel = el('select');
  ['tight', 'average', 'leaky'].forEach((l) => leakSel.appendChild(opt(l, labelFor('leakiness', l, lang), l === s.home.leakiness)));
  leakSel.addEventListener('change', (e) => setState({ home: { ...s.home, leakiness: e.target.value } }));

  const citySel = el('select');
  Object.entries(PRESET_CITIES).forEach(([k, c]) => citySel.appendChild(opt(k, `${c.name} (${c.lat}, ${c.lon})`, k === s.city)));
  citySel.addEventListener('change', (e) => {
    const d = PRESET_CITIES[e.target.value];
    if (d) setState({ city: e.target.value, latitude: d.lat, longitude: d.lon });
  });

  const homeRow = el('div', 'field-row');
  homeRow.append(field('home-leakiness-select', t('draughtyQuestion', lang), leakSel, 'Affects outdoor smoke infiltration'), field('city-preset-select', t('cityPreset', lang), citySel, 'Forecast location for smog calculations'));

  const pF = el('div', 'field');
  const pLbl = el('label', '', ` ${t('purifier', lang)}`);
  pLbl.htmlFor = 'home-purifier-chk';
  const pChk = el('input');
  pChk.type = 'checkbox';
  pChk.id = 'home-purifier-chk';
  pChk.checked = s.home.purifier;
  pChk.addEventListener('change', (e) => setState({ home: { ...s.home, purifier: e.target.checked } }));
  pLbl.prepend(pChk);
  const pHelp = el('small', 'help-text', 'Used in ventilation and indoor simulation logic.');
  pHelp.id = 'home-purifier-help';
  pChk.setAttribute('aria-describedby', pHelp.id);
  pF.append(pLbl, pHelp);
  c2.append(homeRow, pF);
  container.appendChild(c2);

  // Card 3: Your budget
  const c3 = el('div', 'card');
  c3.appendChild(el('h3', '', t('yourBudget', lang)));

  const bF = el('div', 'field');
  const bLbl = el('label', '', `₹${s.budgetInr} per month`);
  bLbl.htmlFor = 'budget-slider';
  bLbl.id = 'budget-amount-label';

  const bRow = el('div', 'field-row');
  const bRange = el('input');
  bRange.type = 'range';
  bRange.id = 'budget-slider';
  bRange.min = '0';
  bRange.max = '20000';
  bRange.step = '100';
  bRange.value = String(s.budgetInr);
  const bNum = el('input');
  bNum.type = 'number';
  bNum.id = 'budget-number';
  bNum.min = '0';
  bNum.max = '100000';
  bNum.value = String(s.budgetInr);

  const bHelp = el('small', 'help-text', t('budgetHelp', lang));
  bHelp.id = 'budget-change-help';
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
  container.appendChild(c3);

  // Primary button at bottom
  const navDiv = el('div', 'form-actions');
  const nextBtn = el('button', 'btn primary btn-primary', t('nextYourDay', lang));
  nextBtn.type = 'button';
  nextBtn.id = 'next-to-ledger-btn';
  navDiv.appendChild(nextBtn);
  container.appendChild(navDiv);
}
