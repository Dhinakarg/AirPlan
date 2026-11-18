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
  const el = document.getElementById('status-announcer');
  if (!el) {
    return;
  }
  el.setAttribute('aria-live', priority);
  el.textContent = '';
  // Slight tick to ensure assistive tech detects textContent mutation
  setTimeout(() => {
    el.textContent = message;
  }, 50);
}

/**
 * Toggle high-contrast rendering mode for visual clarity.
 * @param {boolean} enable - Whether high contrast should be turned on.
 * @returns {boolean} Current high-contrast state.
 */
export function toggleHighContrast(enable) {
  const isEnabled = enable !== undefined ? enable : !document.body.classList.contains('high-contrast');
  if (isEnabled) {
    document.body.classList.add('high-contrast');
  } else {
    document.body.classList.remove('high-contrast');
  }
  announce(isEnabled ? 'High contrast mode enabled' : 'High contrast mode disabled');
  return isEnabled;
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

