/**
 * @fileoverview Accessibility utilities for screen readers, live announcements, and focus management.
 */

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
  setTimeout(() => {
    el.textContent = message;
  }, 50);
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
    return;
  }
  el.classList.remove('sr-only');
  el.textContent = message;
  setFocus(el);
  announce(`Error: ${message}`, 'assertive');
}

/**
 * Toggle high-contrast rendering mode for visual clarity.
 * @param {boolean} [enable] - Whether high contrast should be turned on.
 * @returns {boolean} Current high-contrast state.
 */
export function toggleHighContrast(enable) {
  if (typeof document === 'undefined') return false;
  const isEnabled =
    enable !== undefined ? enable : !document.body.classList.contains('high-contrast');
  if (isEnabled) {
    document.body.classList.add('high-contrast');
  } else {
    document.body.classList.remove('high-contrast');
  }
  announce(isEnabled ? 'High contrast mode enabled' : 'High contrast mode disabled');
  return isEnabled;
}

/**
 * Toggle simple-language plain styling mode.
 * @param {boolean} [enable] - State of simple language mode.
 * @returns {boolean} Current state.
 */
export function toggleSimpleLanguage(enable) {
  if (typeof document === 'undefined') return false;
  const isEnabled =
    enable !== undefined ? enable : !document.body.classList.contains('plain-language');
  if (isEnabled) {
    document.body.classList.add('plain-language');
  } else {
    document.body.classList.remove('plain-language');
  }
  announce(isEnabled ? 'Plain language mode enabled' : 'Plain language mode disabled');
  return isEnabled;
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
 * @returns {boolean}
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
  if (!isSpeechSupported()) return;
  window.speechSynthesis.cancel();
  if (!text) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-US';
  window.speechSynthesis.speak(utterance);
}

/**
 * Cancel active speech synthesis.
 * @returns {void}
 */
export function stopSpeaking() {
  if (!isSpeechSupported()) return;
  window.speechSynthesis.cancel();
}

/**
 * Safely move keyboard focus to an element.
 * @param {HTMLElement | null} element - Target element to focus.
 * @returns {void}
 */
export function setFocus(element) {
  if (element && typeof element.focus === 'function') {
    element.focus();
  }
}
