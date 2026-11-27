/**
 * @fileoverview Screen 2: Day Ledger routine editor, 24h strip, and simulation.
 */

import { announce, showError } from '../a11y.js';
import { simulateRoutine } from '../api.js';
import { buildSelect, el } from '../dom.js';
import { t } from '../i18n.js';
import { getState, setState } from '../state.js';
import { SHORT_ACT, SHORT_MODE, analyzeRoutineCoverage, sortRoutine, summarizeRoutineText } from './ledger_helpers.js';

const ACTIVITIES = Object.keys(SHORT_ACT);
const MODES = Object.keys(SHORT_MODE);
const HOURS = Array.from({ length: 25 }, (_, i) => ({ val: String(i), label: `${i}:00` }));

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
  const sSel = buildSelect({ id: `b-${bIdx}-s`, 'aria-label': `Start ${bIdx + 1}` }, HOURS, block.start_hour, (v) => patch('start_hour', Number(v)));
  const eSel = buildSelect({ id: `b-${bIdx}-e`, 'aria-label': `End ${bIdx + 1}` }, HOURS, block.end_hour, (v) => patch('end_hour', Number(v)));
  const aSel = buildSelect({ id: `b-${bIdx}-a`, 'aria-label': `Activity ${bIdx + 1}` }, ACTIVITIES.map((a) => ({ val: a, label: SHORT_ACT[a] })), block.activity, (v) => patch('activity', v));
  const mSel = buildSelect({ id: `b-${bIdx}-m`, 'aria-label': `Mode ${bIdx + 1}` }, MODES.map((m) => ({ val: m, label: SHORT_MODE[m] })), block.mode, (v) => patch('mode', v));
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
    const act = SHORT_ACT[b.activity] || b.activity;
    const label = dur >= 3 ? `${act} (${dur}h)` : `${dur}h`;
    const seg = el('div', 'day-strip-seg', label);
    seg.title = `${b.start_hour}:00–${b.end_hour}:00 ${act} (${dur}h)`;
    seg.style.flex = String(dur);
    strip.appendChild(seg);
  });
  return [strip, el('p', 'sr-only', summarizeRoutineText(routine))];
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
    const selRow = el('div', 'field'), selLabel = el('label', '', t('planningFor', lang));
    selLabel.htmlFor = 'active-member-select';
    const memSel = buildSelect({ id: 'active-member-select', 'aria-label': t('planningFor', lang) }, s.members.map((m, i) => ({ val: String(i), label: m.name })), String(activeIdx), (v) => setState({ activeMemberIndex: Number(v) }));
    selRow.append(selLabel, memSel);
    mainCol.appendChild(selRow);
  }

  const hdrRow = el('div', 'routine-block-row ledger-col-headers form-label');
  [t('colStart', lang), t('colEnd', lang), t('activity', lang), t('colMode', lang), ''].forEach((lbl) => hdrRow.appendChild(el('span', '', lbl)));
  const blocksList = el('div', 'blocks-list');
  blocksList.appendChild(hdrRow);
  cur.routine.forEach((b, i) => blocksList.appendChild(buildBlockRow(b, i, cur.routine, activeIdx)));
  mainCol.appendChild(blocksList);

  const msgEl = Object.assign(el('p', 'form-error', ''), { id: 'ledger-msg' });
  msgEl.setAttribute('role', 'alert');
  const actionsRow = el('div', 'actions');
  if (cur.routine.length < 12) {
    const addBtn = Object.assign(el('button', 'btn btn-secondary', t('addBlockShort', lang)), { type: 'button' });
    addBtn.addEventListener('click', () => {
      if (cov.covered >= 24) { msgEl.textContent = t('ledgerFullError', lang); return; }
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
  const planBtn = Object.assign(el('button', 'btn primary btn-primary', t('nextYourPlan', lang)), { type: 'button' });
  planBtn.addEventListener('click', () => document.getElementById('step-btn-3')?.click());
  actionsRow.append(suggestBtn, planBtn);
  mainCol.append(msgEl, actionsRow);

  if (s.simulationResult) {
    const resBox = el('div', 'card callout-card');
    resBox.append(el('h3', '', `Counterfactual Day: Index ${s.simulationResult.index_after} (Saved ${s.simulationResult.dose_saved_ug} µg)`), el('p', 'provenance-tag', `${s.simulationResult.provenance.text} [Confidence: ${s.simulationResult.provenance.confidence}]`));
    mainCol.appendChild(resBox);
  }

  const aside = el('aside', 'step-aside'), sumCard = el('div', 'card summary-card'), dl = el('dl', 'summary-list');
  sumCard.appendChild(el('h3', '', t('dailySchedule', lang)));
  const addItem = (dt, dd) => { const it = el('div', 'summary-item'); it.append(el('dt', '', dt), el('dd', '', dd)); dl.appendChild(it); };
  addItem(t('activeMember', lang), cur.name);
  addItem(t('dayCoverage', lang), cov.covered === 24 ? '24 / 24 hrs ✓' : `${cov.covered} / 24 hrs`);
  addItem(t('blocksLabel', lang), `${cur.routine.length} ${t('timeSlots', lang)}`);
  addItem(t('outdoorExposure', lang), `${cur.routine.filter((b) => b.mode === 'walk' || b.mode === 'outdoor').length}`);
  sumCard.appendChild(dl); aside.appendChild(sumCard); layout.append(mainCol, aside); container.appendChild(layout);
}
