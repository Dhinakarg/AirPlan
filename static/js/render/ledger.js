/**
 * @fileoverview Screen 2: Day Ledger routine editor and counterfactual suggestion.
 */

import { announce, showError } from '../a11y.js';
import { simulateRoutine } from '../api.js';
import { el } from '../dom.js';
import { labelFor, t } from '../i18n.js';
import { getState, setState } from '../state.js';
import { analyzeRoutineCoverage, sortRoutine } from './ledger_helpers.js';

const ACTIVITIES = ['sleep', 'rest', 'light', 'walk', 'exercise', 'cook'];
const MODES = ['home', 'walk', 'cycle', 'metro', 'bus', 'auto_rickshaw', 'car', 'outdoor'];
const HOURS = Array.from({ length: 25 }, (_, i) => ({ val: String(i), label: `${i}:00` }));

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

function updateMemberRoutine(memberIdx, newRoutine) {
  const members = [...getState().members];
  members[memberIdx] = { ...members[memberIdx], routine: sortRoutine(newRoutine) };
  setState({ members });
}

function buildBlockRow(block, bIdx, routine, activeIdx, lang) {
  const row = el('div', 'routine-block-row card form-row');
  const patch = (key, val) => {
    const u = routine.map((b, i) => (i === bIdx ? { ...b, [key]: val } : b));
    updateMemberRoutine(activeIdx, u);
  };
  const sSel = makeSel(`Start ${bIdx + 1}`, HOURS, block.start_hour, (v) => patch('start_hour', Number(v)));
  const eSel = makeSel(`End ${bIdx + 1}`, HOURS, block.end_hour, (v) => patch('end_hour', Number(v)));
  const aSel = makeSel(`Activity ${bIdx + 1}`, ACTIVITIES.map((a) => ({ val: a, label: labelFor('activity', a, lang) })), block.activity, (v) => patch('activity', v));
  const mSel = makeSel(`Mode ${bIdx + 1}`, MODES.map((m) => ({ val: m, label: labelFor('mode', m, lang) })), block.mode, (v) => patch('mode', v));
  const rmBtn = Object.assign(el('button', 'btn ghost', '✕'), { type: 'button', disabled: routine.length <= 1 });
  rmBtn.setAttribute('aria-label', `Delete block ${bIdx + 1}`);
  rmBtn.addEventListener('click', () => updateMemberRoutine(activeIdx, routine.filter((_, i) => i !== bIdx)));
  row.append(sSel, eSel, aSel, mSel, rmBtn);
  return row;
}

/**
 * Render Day Ledger routine configuration screen into container.
 *
 * @param {HTMLElement} container - Target container element.
 * @returns {void}
 */
export function renderLedgerScreen(container) {
  container.replaceChildren();
  const s = getState(), lang = s.language;
  const activeIdx = s.activeMemberIndex || 0;
  const currentMember = s.members[activeIdx] || s.members[0];
  const cov = analyzeRoutineCoverage(currentMember.routine);

  const layout = el('div', 'step-layout'), mainCol = el('div', 'step-main');
  mainCol.append(
    el('h2', '', `${t('ledgerTitle', lang)} — ${currentMember.name}`),
    el('p', 'help-text', 'Map 24 hours from 0:00 to 24:00. Slots auto-sort by start time; use ✕ to remove a slot.'),
  );

  if (s.members.length > 1) {
    const selRow = el('div', 'field'), selLabel = el('label', '', `${t('memberName', lang)}:`);
    selLabel.htmlFor = 'active-member-select';
    const memSel = makeSel('Select Member', s.members.map((m, i) => ({ val: String(i), label: m.name })), String(activeIdx), (v) => setState({ activeMemberIndex: Number(v) }));
    memSel.id = 'active-member-select';
    selRow.append(selLabel, memSel);
    mainCol.appendChild(selRow);
  }

  const hdrRow = el('div', 'routine-block-row form-label');
  [t('startHour', lang), t('endHour', lang), t('activity', lang), t('mode', lang), ''].forEach((lbl) => hdrRow.appendChild(el('span', '', lbl)));
  const blocksList = el('div', 'blocks-list');
  blocksList.appendChild(hdrRow);
  currentMember.routine.forEach((b, bIdx) => blocksList.appendChild(buildBlockRow(b, bIdx, currentMember.routine, activeIdx, lang)));
  mainCol.appendChild(blocksList);

  const msgEl = Object.assign(el('p', 'form-error', ''), { id: 'ledger-msg' });
  msgEl.setAttribute('role', 'alert');
  const actionsRow = el('div', 'actions');
  if (currentMember.routine.length < 12) {
    const addBtn = Object.assign(el('button', 'btn btn-secondary', `+ ${t('addBlock', lang)}`), { type: 'button' });
    addBtn.addEventListener('click', () => {
      if (cov.covered >= 24) {
        msgEl.textContent = 'All 24 hours are already covered. Remove (✕) or shorten a slot first.';
        return;
      }
      updateMemberRoutine(activeIdx, [...currentMember.routine, { start_hour: cov.gapStart, end_hour: cov.gapEnd, activity: 'light', mode: 'home' }]);
    });
    actionsRow.appendChild(addBtn);
  }

  const suggestBtn = Object.assign(el('button', 'btn btn-secondary', `💡 ${t('suggestBetterDay', lang)}`), { type: 'button' });
  suggestBtn.addEventListener('click', async () => {
    announce('Optimizing routine...');
    try {
      const alt = currentMember.routine.map((b) => (b.activity === 'exercise' && b.mode === 'outdoor' ? { ...b, mode: 'home' } : { ...b }));
      const sim = await simulateRoutine({ base_routine: currentMember.routine, alt_routine: alt, home: s.home, age_group: currentMember.age_group, latitude: s.latitude, longitude: s.longitude });
      setState({ simulationResult: sim });
      announce(`Simulation: index reduced to ${sim.index_after}.`);
    } catch (err) { showError(err instanceof Error ? err.message : 'Simulation failed'); }
  });
  const planBtn = Object.assign(el('button', 'btn primary btn-primary', 'Next: your plan →'), { type: 'button' });
  planBtn.addEventListener('click', () => document.getElementById('step-btn-3')?.click());
  actionsRow.append(suggestBtn, planBtn);
  mainCol.append(msgEl, actionsRow);

  if (s.simulationResult) {
    const resBox = el('div', 'card callout-card');
    resBox.append(el('h3', '', `Counterfactual Day: Index ${s.simulationResult.index_after} (Saved ${s.simulationResult.dose_saved_ug} µg)`), el('p', 'provenance-tag', `${s.simulationResult.provenance.text} [Confidence: ${s.simulationResult.provenance.confidence}]`));
    mainCol.appendChild(resBox);
  }

  const aside = el('aside', 'step-aside'), sumCard = el('div', 'card summary-card'), dl = el('dl', 'summary-list');
  sumCard.appendChild(el('h3', '', 'Daily Schedule'));
  const addItem = (dt, dd) => { const it = el('div', 'summary-item'); it.append(el('dt', '', dt), el('dd', '', dd)); dl.appendChild(it); };
  addItem('Active member', currentMember.name);
  addItem('Day coverage', cov.covered === 24 ? '24 / 24 hrs ✓' : `${cov.covered} / 24 hrs (fill gaps)`);
  addItem('Blocks', `${currentMember.routine.length} time slots`);
  addItem('Outdoor exposure', `${currentMember.routine.filter((b) => b.mode === 'walk' || b.mode === 'outdoor').length} blocks`);
  sumCard.appendChild(dl);
  aside.appendChild(sumCard);
  layout.append(mainCol, aside);
  container.appendChild(layout);
}
