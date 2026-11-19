/**
 * @fileoverview Accessibility utilities for screen readers, live announcements, and focus management.
 */

const triggerMap = new WeakMap();

/**
 * Deliver dynamic text announcements to assistive technology screen readers.
 * @param {string} message - Announcement string.
 * @param {'polite' | 'assertive'} [priority='polite'] - ARIA live urgency level.
 * @returns {void}
 */
export function announce(message, priority = 'polite') {
  if (typeof document === 'undefined') return;
  const el = document.getElementById('status-announcer');
  if (!el) return;
  el.setAttribute('aria-live', priority);
  el.textContent = '';
  setTimeout(() => { el.textContent = message; }, 50);
}

/**
 * Display error banner in assertive role="alert" container and move focus.
 * @param {string | null} message - Error message or null to clear.
 * @returns {void}
 */
export function showError(message) {
  if (typeof document === 'undefined') return;
  const el = document.getElementById('error-alert');
  if (!el) return;
  if (!message) {
    el.classList.add('sr-only');
    el.textContent = '';
  } else {
    el.classList.remove('sr-only');
    el.textContent = message;
    setFocus(el);
    announce(`Error: ${message}`, 'assertive');
  }
}

/**
 * Toggle high-contrast rendering mode for visual clarity.
 * @param {boolean} [enable] - Whether high contrast should be turned on.
 * @returns {boolean} Current high-contrast state.
 */
export function toggleHighContrast(enable) {
  if (typeof document === 'undefined') return false;
  const on = enable !== undefined ? enable : !document.body.classList.contains('high-contrast');
  document.body.classList.toggle('high-contrast', on);
  announce(on ? 'High contrast mode enabled' : 'High contrast mode disabled');
  return on;
}

/**
 * Toggle simple-language plain styling mode.
 * @param {boolean} [enable] - State of simple language mode.
 * @returns {boolean} Current state.
 */
export function toggleSimpleLanguage(enable) {
  if (typeof document === 'undefined') return false;
  const on = enable !== undefined ? enable : !document.body.classList.contains('plain-language');
  document.body.classList.toggle('plain-language', on);
  announce(on ? 'Plain language mode enabled' : 'Plain language mode disabled');
  return on;
}

/**
 * Set root font size scale.
 * @param {'normal' | 'large' | 'larger'} size - Font scale level.
 * @returns {void}
 */
export function setTextSize(size) {
  if (typeof document === 'undefined') return;
  const scales = { normal: '100%', large: '115%', larger: '130%' };
  document.documentElement.style.fontSize = scales[size] || '100%';
  announce(`Text size set to ${size}`);
}

/**
 * Check if Web Speech API is supported.
 * @returns {boolean} True if speech synthesis is available.
 */
export function isSpeechSupported() {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
}

/**
 * Speak text aloud using speechSynthesis.
 * @param {string} text - Text to synthesize.
 * @param {'en' | 'hi'} [lang='en'] - Spoken language.
 * @returns {void}
 */
export function speakText(text, lang = 'en') {
  if (!isSpeechSupported() || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-US';
  window.speechSynthesis.speak(utterance);
}

/**
 * Cancel active speech synthesis.
 * @returns {void}
 */
export function stopSpeaking() {
  if (isSpeechSupported()) window.speechSynthesis.cancel();
}

/**
 * Safely move keyboard focus to an element.
 * @param {HTMLElement | null} element - Target element to focus.
 * @returns {void}
 */
export function setFocus(element) {
  if (element && typeof element.focus === 'function') element.focus();
}

/**
 * Open accessible dialog with focus trap and return-focus behavior.
 * @param {HTMLDialogElement} dialog - Dialog element.
 * @param {HTMLElement} [trigger] - Element to return focus to upon closing.
 * @returns {() => void} Cleanup handler.
 */
export function openModalDialog(dialog, trigger) {
  if (!dialog) return () => {};
  const active = trigger || (document.activeElement instanceof HTMLElement ? document.activeElement : null);
  if (active) triggerMap.set(dialog, active);
  if (typeof dialog.showModal === 'function') dialog.showModal();
  else dialog.setAttribute('open', '');

  const focusables = dialog.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (focusables.length > 0 && focusables[0] instanceof HTMLElement) focusables[0].focus();

  const onKey = (e) => {
    if (e.key === 'Escape') { e.preventDefault(); closeModalDialog(dialog); return; }
    if (e.key !== 'Tab') return;
    const items = Array.from(focusables).filter(el => !el.hasAttribute('disabled'));
    if (!items.length) return;
    if (e.shiftKey && document.activeElement === items[0]) {
      e.preventDefault(); items[items.length - 1].focus();
    } else if (!e.shiftKey && document.activeElement === items[items.length - 1]) {
      e.preventDefault(); items[0].focus();
    }
  };
  dialog.addEventListener('keydown', onKey);
  announce('Settings dialog opened');
  return () => dialog.removeEventListener('keydown', onKey);
}

/**
 * Close accessible dialog and return focus to triggering element.
 * @param {HTMLDialogElement} dialog - Target dialog element.
 * @returns {void}
 */
export function closeModalDialog(dialog) {
  if (!dialog) return;
  if (typeof dialog.close === 'function') dialog.close();
  else dialog.removeAttribute('open');
  const trigger = triggerMap.get(dialog);
  if (trigger && typeof trigger.focus === 'function') trigger.focus();
  announce('Settings dialog closed');
}
