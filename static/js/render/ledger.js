/**
 * @fileoverview Screen 2: Day Ledger routine editor and counterfactual suggestion.
 */

import { announce, showError } from '../a11y.js';
import { simulateRoutine } from '../api.js';
import { labelFor, t } from '../i18n.js';
import { getState, setState } from '../state.js';

const ACTIVITIES = ['sleep', 'rest', 'light', 'walk', 'exercise', 'cook'];
const MODES = ['home', 'walk', 'cycle', 'metro', 'bus', 'auto_rickshaw', 'car', 'outdoor'];
const HOURS = Array.from({ length: 25 }, (_, i) => ({ val: String(i), label: `${i}:00` }));

function el(tag, cls = '', text = '') {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
}

function makeSel(ariaLabel, options, currentVal, onChange) {
  const sel = document.createElement('select');
  sel.setAttribute('aria-label', ariaLabel);
  options.forEach((o) => {
    const opt = document.createElement('option');
    opt.value = typeof o === 'object' ? o.val : o;
    opt.textContent = typeof o === 'object' ? o.label : o;
    if (opt.value === String(currentVal)) opt.selected = true;
    sel.appendChild(opt);
  });
  sel.addEventListener('change', (e) => onChange(e.target.value));
  return sel;
}

export function renderLedgerScreen(container) {
  container.replaceChildren();
  const s = getState(), lang = s.language;
  const activeIdx = s.activeMemberIndex || 0;
  const currentMember = s.members[activeIdx] || s.members[0];

  const layout = el('div', 'step-layout'), mainCol = el('div', 'step-main');
  mainCol.append(el('h2', '', `${t('ledgerTitle', lang)} — ${currentMember.name}`));

  if (s.members.length > 1) {
    const selRow = el('div', 'field'), selLabel = el('label', '', `${t('memberName', lang)}:`);
    selLabel.htmlFor = 'active-member-select';
    const memOpts = s.members.map((m, i) => ({ val: String(i), label: m.name }));
    const memSel = makeSel('Select Member', memOpts, String(activeIdx), (v) => setState({ activeMemberIndex: Number(v) }));
    memSel.id = 'active-member-select';
    selRow.append(selLabel, memSel);
    mainCol.appendChild(selRow);
  }

  const blocksList = el('div', 'blocks-list');
  currentMember.routine.forEach((block, bIdx) => {
    const row = el('div', 'routine-block-row card form-row');
    const sSel = makeSel(`Start ${bIdx + 1}`, HOURS, block.start_hour, (v) => {
      const u = [...currentMember.routine]; u[bIdx].start_hour = Number(v); updateMemberRoutine(activeIdx, u);
    });
    const eSel = makeSel(`End ${bIdx + 1}`, HOURS, block.end_hour, (v) => {
      const u = [...currentMember.routine]; u[bIdx].end_hour = Number(v); updateMemberRoutine(activeIdx, u);
    });
    const actOpts = ACTIVITIES.map((a) => ({ val: a, label: labelFor('activity', a, lang) }));
    const aSel = makeSel(`Activity ${bIdx + 1}`, actOpts, block.activity, (v) => {
      const u = [...currentMember.routine]; u[bIdx].activity = v; updateMemberRoutine(activeIdx, u);
    });
    const modeOpts = MODES.map((m) => ({ val: m, label: labelFor('mode', m, lang) }));
    const mSel = makeSel(`Mode ${bIdx + 1}`, modeOpts, block.mode, (v) => {
      const u = [...currentMember.routine]; u[bIdx].mode = v; updateMemberRoutine(activeIdx, u);
    });

    const rmBtn = el('button', 'btn ghost', '✕');
    rmBtn.type = 'button';
    rmBtn.setAttribute('aria-label', `Delete block ${bIdx + 1}`);
    rmBtn.disabled = currentMember.routine.length <= 1;
    rmBtn.addEventListener('click', () => {
      const u = [...currentMember.routine]; u.splice(bIdx, 1); updateMemberRoutine(activeIdx, u);
    });
    row.append(sSel, eSel, aSel, mSel, rmBtn);
    blocksList.appendChild(row);
  });
  mainCol.appendChild(blocksList);

  const actionsRow = el('div', 'actions');
  if (currentMember.routine.length < 12) {
    const addBtn = el('button', 'btn btn-secondary', `+ ${t('addBlock', lang)}`);
    addBtn.type = 'button';
    addBtn.addEventListener('click', () => {
      const last = currentMember.routine[currentMember.routine.length - 1];
      const startH = last ? last.end_hour : 0;
      updateMemberRoutine(activeIdx, [...currentMember.routine, { start_hour: startH, end_hour: Math.min(24, startH + 2), activity: 'light', mode: 'home' }]);
    });
    actionsRow.appendChild(addBtn);
  }

  const suggestBtn = el('button', 'btn btn-secondary', `💡 ${t('suggestBetterDay', lang)}`);
  suggestBtn.type = 'button';
  suggestBtn.addEventListener('click', async () => {
    announce('Optimizing routine...');
    try {
      const alt = currentMember.routine.map((b) => b.activity === 'exercise' && b.mode === 'outdoor' ? { ...b, activity: 'exercise', mode: 'home' } : { ...b });
      const sim = await simulateRoutine({ base_routine: currentMember.routine, alt_routine: alt, home: s.home, age_group: currentMember.age_group, latitude: s.latitude, longitude: s.longitude });
      setState({ simulationResult: sim });
      announce(`Simulation: index reduced to ${sim.index_after}.`);
    } catch (err) { showError(err instanceof Error ? err.message : 'Simulation failed'); }
  });
  actionsRow.appendChild(suggestBtn);

  const planBtn = el('button', 'btn primary btn-primary', `Next: your plan →`);
  planBtn.type = 'button';
  planBtn.addEventListener('click', () => {
    const resultsTab = document.getElementById('step-btn-3');
    if (resultsTab) resultsTab.click();
  });
  actionsRow.appendChild(planBtn);
  mainCol.appendChild(actionsRow);

  if (s.simulationResult) {
    const resBox = el('div', 'card callout-card');
    resBox.append(el('h3', '', `Counterfactual Day: Index ${s.simulationResult.index_after} (Saved ${s.simulationResult.dose_saved_ug} µg)`), el('p', 'provenance-tag', `${s.simulationResult.provenance.text} [Confidence: ${s.simulationResult.provenance.confidence}]`));
    mainCol.appendChild(resBox);
  }
  layout.appendChild(mainCol);

  // Aside
  const aside = el('aside', 'step-aside'), sumCard = el('div', 'card summary-card'), dl = el('dl', 'summary-list');
  sumCard.appendChild(el('h3', '', 'Daily Schedule'));
  const addItem = (dt, dd) => { const it = el('div', 'summary-item'); it.append(el('dt', '', dt), el('dd', '', dd)); dl.appendChild(it); };
  addItem('Active member', currentMember.name);
  addItem('Blocks', `${currentMember.routine.length} time slots`);
  addItem('Outdoor exposure', `${currentMember.routine.filter(b => b.mode === 'walk' || b.mode === 'outdoor').length} blocks`);
  sumCard.append(dl, el('p', 'summary-hint', 'Next: generate your clean-air plan and view hour-by-hour exposure.'));
  aside.appendChild(sumCard);
  layout.appendChild(aside);

  container.appendChild(layout);
}

function updateMemberRoutine(memberIdx, newRoutine) {
  const members = [...getState().members];
  members[memberIdx].routine = newRoutine;
  setState({ members });
}
