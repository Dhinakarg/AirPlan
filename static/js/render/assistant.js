/**
 * @fileoverview Screen 6: Ask AirPlan assistant Q&A with clinical red-flag alert.
 */

import { announce, setFocus, showError } from '../a11y.js';
import { askAssistant } from '../api.js';
import { el } from '../dom.js';
import { t } from '../i18n.js';
import { getState, setState } from '../state.js';

function renderAssistantResult(container, res, lang) {
  if (!res) return;
  const resultBox = el('div');
  resultBox.style.marginTop = '24px';

  if (res.is_red_flag) {
    resultBox.className = 'card emergency-alert';
    resultBox.setAttribute('role', 'alert');
    resultBox.tabIndex = -1;
    const alertHdr = el('h3', '', `🚨 ${t('emergencyAlert', lang)}`);
    const sum = el('p', '', res.summary);
    sum.style.fontWeight = '700';
    resultBox.append(alertHdr, sum, el('p', '', res.answer));
    setFocus(resultBox);
  } else {
    resultBox.className = 'card callout-card';
    resultBox.appendChild(el('h3', '', res.summary));
    if (res.tips?.length) {
      const ul = el('ul');
      res.tips.forEach((tip) => ul.appendChild(el('li', '', tip)));
      resultBox.appendChild(ul);
    }
    resultBox.appendChild(el('p', '', res.answer));
  }
  container.appendChild(resultBox);
}

/**
 * Render Ask AirPlan Screen.
 *
 * @param {HTMLElement} container - Target container element.
 * @returns {void}
 */
export function renderAssistantScreen(container) {
  container.replaceChildren();
  const s = getState(), lang = s.language;
  container.appendChild(el('h3', '', t('assistantTitle', lang)));

  const form = el('form', 'form-grid card');
  form.noValidate = true;

  const qIn = el('textarea');
  Object.assign(qIn, {
    id: 'assistant-question-input',
    rows: 3,
    maxLength: 300,
    placeholder: 'e.g. When is the safest hour to open windows or exercise today?',
  });
  const qLbl = el('label', '', t('askQuestion', lang));
  qLbl.htmlFor = qIn.id;
  form.appendChild(el('div', 'form-group', [qLbl, qIn]));

  const askBtn = el('button', 'btn btn-primary', `💬 ${t('askButton', lang)}`);
  askBtn.type = 'submit';
  form.appendChild(askBtn);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const q = qIn.value.trim();
    if (!q) return;

    announce('Consulting clean-air assistant...');
    try {
      const facts = s.planResult
        ? {
            window_start: s.planResult.ventilation_window?.start_hour || 13,
            window_end: s.planResult.ventilation_window?.end_hour || 15,
            index_after: 70,
          }
        : {};
      const res = await askAssistant(q, facts, lang);
      setState({ assistantResult: res });
      announce('Assistant response received.');
    } catch (err) {
      showError(err instanceof Error ? err.message : 'Assistant inquiry failed');
    }
  });

  container.appendChild(form);
  renderAssistantResult(container, s.assistantResult, lang);
}
