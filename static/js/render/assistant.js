/**
 * @fileoverview Screen 6: Ask AirPlan assistant Q&A with clinical red-flag alert.
 */

import { announce, setFocus, showError } from '../a11y.js';
import { askAssistant } from '../api.js';
import { t } from '../i18n.js';
import { getState, setState } from '../state.js';

/**
 * Render Ask AirPlan Screen.
 * @param {HTMLElement} container - Target container.
 * @returns {void}
 */
export function renderAssistantScreen(container) {
  container.replaceChildren();
  const s = getState();
  const lang = s.language;

  const title = document.createElement('h3');
  title.textContent = t('assistantTitle', lang);
  container.appendChild(title);

  const form = document.createElement('form');
  form.className = 'form-grid card';
  form.noValidate = true;

  const qGroup = document.createElement('div');
  qGroup.className = 'form-group';
  const qLbl = document.createElement('label');
  qLbl.htmlFor = 'assistant-question-input';
  qLbl.textContent = t('askQuestion', lang);

  const qIn = document.createElement('textarea');
  qIn.id = 'assistant-question-input';
  qIn.rows = 3;
  qIn.maxLength = 300;
  qIn.placeholder = 'e.g. When is the safest hour to open windows or exercise today?';

  qGroup.appendChild(qLbl);
  qGroup.appendChild(qIn);
  form.appendChild(qGroup);

  const askBtn = document.createElement('button');
  askBtn.type = 'submit';
  askBtn.className = 'btn btn-primary';
  askBtn.textContent = `💬 ${t('askButton', lang)}`;
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

  // Render assistant answer
  renderAssistantResult(container, s.assistantResult, lang);
}

function renderAssistantResult(container, res, lang) {
  if (!res) return;

  const resultBox = document.createElement('div');
  resultBox.style.marginTop = '24px';

  // Red-flag answers use role="alert"
  if (res.is_red_flag) {
    resultBox.className = 'card emergency-alert';
    resultBox.setAttribute('role', 'alert');
    resultBox.tabIndex = -1;

    const alertHdr = document.createElement('h3');
    alertHdr.textContent = `🚨 ${t('emergencyAlert', lang)}`;
    const sum = document.createElement('p');
    sum.style.fontWeight = '700';
    sum.textContent = res.summary;
    const ans = document.createElement('p');
    ans.textContent = res.answer;

    resultBox.appendChild(alertHdr);
    resultBox.appendChild(sum);
    resultBox.appendChild(ans);
    setFocus(resultBox);
  } else {
    resultBox.className = 'card callout-card';

    const sumHdr = document.createElement('h3');
    sumHdr.textContent = res.summary;
    resultBox.appendChild(sumHdr);

    if (res.tips && res.tips.length > 0) {
      const tipsList = document.createElement('ul');
      res.tips.forEach((tip) => {
        const li = document.createElement('li');
        li.textContent = tip;
        tipsList.appendChild(li);
      });
      resultBox.appendChild(tipsList);
    }

    const ansP = document.createElement('p');
    ansP.textContent = res.answer;
    resultBox.appendChild(ansP);
  }

  container.appendChild(resultBox);
}

