/**
 * @fileoverview Screen 2: Day Ledger routine editor, 24h strip, and simulation.
 */

import { announce, showError } from '../a11y.js';
import { simulateRoutine } from '../api.js';
import { el } from '../dom.js';
import { t } from '../i18n.js';
import { getState, setState } from '../state.js';
import { SHORT_ACT, SHORT_MODE, analyzeRoutineCoverage, sortRoutine, summarizeRoutineText } from './ledger_helpers.js';

const ACTIVITIES = Object.keys(SHORT_ACT);
const MODES = Object.keys(SHORT_MODE);
const HOURS = Array.from({ length: 25 }, (_, i) => ({ val: String(i), label: `${i}:00` }));

function makeSel(id, ariaLabel, options, currentVal, onChange) {
  const sel = document.createElement('select');
  sel.id = id;
  sel.setAttribute('aria-label', ariaLabel);
  options.forEach((o) => {
    const opt = Object.assign(document.createElement('option'), {
      value: typeof o === 'object' ? o.val : o,
      textContent: typeof o === 'object' ? o.label : o,
    });
    if (opt.value === String(currentVal)) opt.selected = true;
    sel.appendChild(opt);
  });
  sel.addEventListener('change', (e) => onChange(e.target.value));
  return sel;
}

function wrapField(lblText, sel) {
  const wrap = el('div', 'ledger-field');
  const lbl = el('label', 'mobile-field-label', lblText);
  lbl.htmlFor = sel.id;
  wrap.append(lbl, sel);
  return wrap;
}

function updateMemberRoutine(memberIdx, newRoutine) {
  const members = [...getState().members];
  members[memberIdx] = { ...members[memberIdx], routine: sortRoutine(newRoutine) };
  setState({ members });
}

function buildBlockRow(block, bIdx, routine, activeIdx) {
  const row = el('div', 'routine-block-row card');
  const patch = (key, val) => updateMemberRoutine(activeIdx, routine.map((b, i) => (i === bIdx ? { ...b, [key]: val } : b)));
  const sSel = makeSel(`b-${bIdx}-s`, `Start ${bIdx + 1}`, HOURS, block.start_hour, (v) => patch('start_hour', Number(v)));
  const eSel = makeSel(`b-${bIdx}-e`, `End ${bIdx + 1}`, HOURS, block.end_hour, (v) => patch('end_hour', Number(v)));
  const aSel = makeSel(`b-${bIdx}-a`, `Activity ${bIdx + 1}`, ACTIVITIES.map((a) => ({ val: a, label: SHORT_ACT[a] })), block.activity, (v) => patch('activity', v));
  const mSel = makeSel(`b-${bIdx}-m`, `Mode ${bIdx + 1}`, MODES.map((m) => ({ val: m, label: SHORT_MODE[m] })), block.mode, (v) => patch('mode', v));
  const rmBtn = Object.assign(el('button', 'btn ghost', '✕'), { type: 'button', disabled: routine.length <= 1 });
  rmBtn.setAttribute('aria-label', `Delete block ${bIdx + 1}`);
  rmBtn.addEventListener('click', () => updateMemberRoutine(activeIdx, routine.filter((_, i) => i !== bIdx)));
  row.append(wrapField('Start', sSel), wrapField('End', eSel), wrapField('Activity', aSel), wrapField('Mode', mSel), rmBtn);
  return row;
}

function buildDayStrip(routine) {
  const strip = el('div', 'day-strip');
  strip.setAttribute('aria-hidden', 'true');
  routine.forEach((b) => {
    const dur = Math.max(1, b.end_hour - b.start_hour);
    const seg = el('div', 'day-strip-seg', `${SHORT_ACT[b.activity] || b.activity} (${dur}h)`);
    seg.style.flex = String(dur);
    strip.appendChild(seg);
  });
  const textEq = el('p', 'help-text', summarizeRoutineText(routine));
  return [strip, textEq];
}

/**
 * Render Day Ledger routine configuration screen into container.
 * @param {HTMLElement} container - Target container element.
 * @returns {void}
 */
export function renderLedgerScreen(container) {
  container.replaceChildren();
  const s = getState(), lang = s.language;
  const activeIdx = s.activeMemberIndex || 0;
  const cur = s.members[activeIdx] || s.members[0];
  const cov = analyzeRoutineCoverage(cur.routine);
  const layout = el('div', 'step-layout'), mainCol = el('div', 'step-main');
  mainCol.append(el('h2', '', `${t('ledgerTitle', lang)} — ${cur.name}`), ...buildDayStrip(cur.routine));

  if (s.members.length > 1) {
    const selRow = el('div', 'field'), selLabel = el('label', '', 'Planning for');
    selLabel.htmlFor = 'active-member-select';
    const memSel = makeSel('active-member-select', 'Planning for', s.members.map((m, i) => ({ val: String(i), label: m.name })), String(activeIdx), (v) => setState({ activeMemberIndex: Number(v) }));
    selRow.append(selLabel, memSel);
    mainCol.appendChild(selRow);
  }

  const hdrRow = el('div', 'routine-block-row ledger-col-headers form-label');
  ['Start', 'End', 'Activity', 'Mode', ''].forEach((lbl) => hdrRow.appendChild(el('span', '', lbl)));
  const blocksList = el('div', 'blocks-list');
  blocksList.appendChild(hdrRow);
  cur.routine.forEach((b, i) => blocksList.appendChild(buildBlockRow(b, i, cur.routine, activeIdx)));
  mainCol.appendChild(blocksList);

  const msgEl = Object.assign(el('p', 'form-error', ''), { id: 'ledger-msg' });
  msgEl.setAttribute('role', 'alert');
  const actionsRow = el('div', 'actions');
  if (cur.routine.length < 12) {
    const addBtn = Object.assign(el('button', 'btn btn-secondary', '+ Add block'), { type: 'button' });
    addBtn.addEventListener('click', () => {
      if (cov.covered >= 24) { msgEl.textContent = 'All 24 hours are covered. Remove (✕) or shorten a slot first.'; return; }
      updateMemberRoutine(activeIdx, [...cur.routine, { start_hour: cov.gapStart, end_hour: cov.gapEnd, activity: 'light', mode: 'home' }]);
    });
    actionsRow.appendChild(addBtn);
  }

  const suggestBtn = Object.assign(el('button', 'btn btn-secondary', `💡 ${t('suggestBetterDay', lang)}`), { type: 'button' });
  suggestBtn.addEventListener('click', async () => {
    announce('Optimizing routine...');
    try {
      const alt = cur.routine.map((b) => (b.activity === 'exercise' && b.mode === 'outdoor' ? { ...b, mode: 'home' } : { ...b }));
      const sim = await simulateRoutine({ base_routine: cur.routine, alt_routine: alt, home: s.home, age_group: cur.age_group, latitude: s.latitude, longitude: s.longitude });
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
  addItem('Active member', cur.name);
  addItem('Day coverage', cov.covered === 24 ? '24 / 24 hrs ✓' : `${cov.covered} / 24 hrs`);
  addItem('Blocks', `${cur.routine.length} time slots`);
  addItem('Outdoor exposure', `${cur.routine.filter((b) => b.mode === 'walk' || b.mode === 'outdoor').length} blocks`);
  sumCard.appendChild(dl); aside.appendChild(sumCard); layout.append(mainCol, aside); container.appendChild(layout);
}
