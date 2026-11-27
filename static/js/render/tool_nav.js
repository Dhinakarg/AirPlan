/**
 * @fileoverview Shared back-to-plan and tool-switcher bar for secondary screens.
 */

import { el } from '../dom.js';
import { t } from '../i18n.js';

const TOOLS = [
  { id: 'screen-detective', icon: '🔍', key: 'navDetective' },
  { id: 'screen-neighbourhood', icon: '🤝', key: 'navNeighbourhood' },
  { id: 'screen-assistant', icon: '💬', key: 'navAssistant' },
];

function navigateTo(screenId) {
  if (typeof document !== 'undefined' && typeof CustomEvent !== 'undefined') {
    document.dispatchEvent(new CustomEvent('airplan:navigate', { detail: screenId }));
  }
}

/**
 * Build a navigation bar with a "Back to Clean-Air Plan" button and quick tool tabs.
 * @param {string} activeId - Currently visible secondary screen ID.
 * @param {string} lang - Active UI language.
 * @returns {HTMLElement}
 */
export function buildToolNav(activeId, lang) {
  const nav = el('nav', { class: 'tool-nav-bar', 'aria-label': 'More tools navigation' });
  const backBtn = Object.assign(el('button', 'btn btn-secondary', t('backToPlan', lang)), { type: 'button' });
  backBtn.addEventListener('click', () => navigateTo('screen-results'));

  const links = el('div', 'tool-nav-links');
  TOOLS.forEach((tool) => {
    const active = tool.id === activeId;
    const btn = Object.assign(el('button', `btn ${active ? 'btn-primary' : 'btn-secondary'}`, `${tool.icon} ${t(tool.key, lang)}`), { type: 'button' });
    if (active) btn.setAttribute('aria-current', 'page');
    btn.addEventListener('click', () => { if (!active) navigateTo(tool.id); });
    links.appendChild(btn);
  });

  nav.append(backBtn, links);
  return nav;
}

