/**
 * @fileoverview Screen 1: Family and Household Setup view renderer.
 */

import { t } from '../i18n.js';
import { PRESET_CITIES, getState, setState } from '../state.js';

function makeSelect(id, label, options, currentVal, onChange) {
  const lbl = document.createElement('label');
  lbl.htmlFor = id;
  lbl.textContent = label;
  const sel = document.createElement('select');
  sel.id = id;
  options.forEach((optVal) => {
    const opt = document.createElement('option');
    opt.value = typeof optVal === 'object' ? optVal.val : optVal;
    opt.textContent = typeof optVal === 'object' ? optVal.label : optVal;
    if (opt.value === currentVal) opt.selected = true;
    sel.appendChild(opt);
  });
  sel.addEventListener('change', (e) => onChange(e.target.value));
  return [lbl, sel];
}

/**
 * Render Family Setup screen inside target container.
 * @param {HTMLElement} container - Target container element.
 * @returns {void}
 */
export function renderFamilyScreen(container) {
  container.replaceChildren();
  const s = getState();
  const lang = s.language;

  // 1. Members List
  const memGroup = document.createElement('div');
  memGroup.className = 'sub-section';
  const memTitle = document.createElement('h3');
  memTitle.textContent = `${t('familyTitle', lang)} (${s.members.length}/6)`;
  memGroup.appendChild(memTitle);

  s.members.forEach((m, idx) => {
    const card = document.createElement('div');
    card.className = 'member-item card';
    const hdr = document.createElement('div');
    hdr.className = 'flex-between';
    const nameLbl = document.createElement('strong');
    nameLbl.textContent = `${m.name} [${m.age_group}, ${m.sensitivity}]`;
    hdr.appendChild(nameLbl);

    if (s.members.length > 1) {
      const rmBtn = document.createElement('button');
      rmBtn.type = 'button';
      rmBtn.className = 'btn btn-sm btn-danger';
      rmBtn.textContent = `✕ ${t('removeMember', lang)}`;
      rmBtn.setAttribute('aria-label', `${t('removeMember', lang)} ${m.name}`);
      rmBtn.addEventListener('click', () => {
        const next = [...s.members];
        next.splice(idx, 1);
        setState({ members: next, activeMemberIndex: 0 });
      });
      hdr.appendChild(rmBtn);
    }
    card.appendChild(hdr);
    memGroup.appendChild(card);
  });

  if (s.members.length < 6) {
    const addRow = document.createElement('div');
    addRow.className = 'form-row';
    const nameIn = document.createElement('input');
    nameIn.type = 'text';
    nameIn.id = 'new-member-name';
    nameIn.placeholder = 'Name';
    nameIn.setAttribute('aria-label', t('memberName', lang));

    const ageSel = document.createElement('select');
    ageSel.id = 'new-member-age';
    ageSel.setAttribute('aria-label', t('ageGroup', lang));
    ['toddler', 'child', 'teen', 'adult', 'senior'].forEach((a) => {
      const opt = document.createElement('option');
      opt.value = opt.textContent = a;
      if (a === 'adult') opt.selected = true;
      ageSel.appendChild(opt);
    });

    const addBtn = document.createElement('button');
    addBtn.type = 'button';
    addBtn.className = 'btn btn-secondary';
    addBtn.textContent = `+ ${t('addMember', lang)}`;
    addBtn.addEventListener('click', () => {
      const val = nameIn.value.trim() || `Member ${s.members.length + 1}`;
      setState({
        members: [
          ...s.members,
          {
            name: val,
            age_group: ageSel.value,
            sensitivity: 'none',
            routine: JSON.parse(JSON.stringify(s.members[0].routine)),
          },
        ],
      });
    });
    addRow.appendChild(nameIn);
    addRow.appendChild(ageSel);
    addRow.appendChild(addBtn);
    memGroup.appendChild(addRow);
  }
  container.appendChild(memGroup);

  // 2. Home Profile & City Location
  const homeGroup = document.createElement('div');
  homeGroup.className = 'sub-section';
  const [leakLbl, leakSel] = makeSelect(
    'home-leakiness-select',
    t('leakiness', lang),
    ['tight', 'average', 'leaky'],
    s.home.leakiness,
    (v) => setState({ home: { ...s.home, leakiness: v } })
  );
  homeGroup.appendChild(leakLbl);
  homeGroup.appendChild(leakSel);

  const purLbl = document.createElement('label');
  purLbl.className = 'checkbox-label';
  purLbl.htmlFor = 'home-purifier-chk';
  const purChk = document.createElement('input');
  purChk.type = 'checkbox';
  purChk.id = 'home-purifier-chk';
  purChk.checked = s.home.purifier;
  purChk.addEventListener('change', (e) =>
    setState({ home: { ...s.home, purifier: e.target.checked } })
  );
  const purSpan = document.createElement('span');
  purSpan.textContent = t('purifier', lang);
  purLbl.appendChild(purChk);
  purLbl.appendChild(purSpan);
  homeGroup.appendChild(purLbl);

  // City preset selection
  const cityOpts = Object.entries(PRESET_CITIES).map(([k, c]) => ({
    val: k,
    label: `${c.name} (${c.lat}, ${c.lon})`,
  }));
  const [cLabel, cSel] = makeSelect(
    'city-preset-select',
    t('cityPreset', lang),
    cityOpts,
    s.city,
    (val) => {
      const d = PRESET_CITIES[val];
      if (d) setState({ city: val, latitude: d.lat, longitude: d.lon });
    }
  );
  homeGroup.appendChild(cLabel);
  homeGroup.appendChild(cSel);

  // Budget slider & number input
  const budgetLbl = document.createElement('label');
  budgetLbl.htmlFor = 'budget-slider';
  budgetLbl.textContent = `${t('budgetInr', lang)}: ₹${s.budgetInr}`;
  const bRow = document.createElement('div');
  bRow.className = 'form-row';

  const bRange = document.createElement('input');
  bRange.type = 'range';
  bRange.id = 'budget-slider';
  bRange.min = '0';
  bRange.max = '20000';
  bRange.step = '100';
  bRange.value = String(s.budgetInr);
  bRange.setAttribute('aria-label', `${t('budgetInr', lang)} slider`);

  const bNum = document.createElement('input');
  bNum.type = 'number';
  bNum.id = 'budget-number';
  bNum.min = '0';
  bNum.max = '100000';
  bNum.value = String(s.budgetInr);
  bNum.setAttribute('aria-label', `${t('budgetInr', lang)} number`);

  const syncBudget = (val) => {
    bRange.value = String(Math.min(20000, val));
    bNum.value = String(val);
    budgetLbl.textContent = `${t('budgetInr', lang)}: ₹${val}`;
    setState({ budgetInr: val });
  };
  bRange.addEventListener('input', (e) => syncBudget(Number(e.target.value)));
  bNum.addEventListener('input', (e) => syncBudget(Number(e.target.value) || 0));

  bRow.appendChild(bRange);
  bRow.appendChild(bNum);
  homeGroup.appendChild(budgetLbl);
  homeGroup.appendChild(bRow);
  container.appendChild(homeGroup);
}
