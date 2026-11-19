/**
 * @fileoverview Internationalization dictionary and translation service.
 */

import { DICTIONARY } from './dictionary.js';

export { DICTIONARY };

/**
 * Retrieve localized translation string by dictionary key.
 *
 * @param {string} key - Dictionary message key.
 * @param {'en' | 'hi'} [lang='en'] - Target locale code.
 * @returns {string} Translated message string or fallback key.
 */
export function t(key, lang = 'en') {
  const entry = DICTIONARY[key];
  return !entry ? key : (lang === 'hi' ? entry.hi : entry.en);
}

/**
 * Resolve display label for domain enumerations without leaking raw keys.
 *
 * @param {string} group - Classification domain group.
 * @param {string} value - Raw enumeration value.
 * @param {'en' | 'hi'} [lang='en'] - Target locale code.
 * @returns {string} Human-readable localized label.
 */
export function labelFor(group, value, lang = 'en') {
  const map = {
    ageGroup: 'enum_age_',
    sensitivity: 'enum_sens_',
    leakiness: 'enum_leak_',
    activity: 'enum_act_',
    mode: 'enum_mode_',
    cookingFuel: 'enum_fuel_',
  };
  const prefix = map[group] || `enum_${group}_`;
  return t(`${prefix}${value}`, lang);
}

/**
 * Format particulate concentration with standard physical unit.
 *
 * @param {number | string} val - Particulate matter concentration.
 * @returns {string} Formatted reading with units.
 */
export function formatConcentration(val) {
  return `${Number(val).toFixed(1)} µg/m³`;
}

/**
 * Categorize PM2.5 concentration into standard regulatory tiers.
 *
 * @param {number} pm25 - Particulate concentration in ug/m3.
 * @returns {{ label: string, icon: string, pattern: string }} Category attributes.
 */
export function getAqiCategory(pm25) {
  if (pm25 <= 30) return { label: 'Good (0-30)', icon: '🟢', pattern: '[Solid Dot]' };
  if (pm25 <= 60) return { label: 'Satisfactory (31-60)', icon: '🟡', pattern: '[Diagonal Slash]' };
  if (pm25 <= 120) return { label: 'Moderate (61-120)', icon: '🟠', pattern: '[Horizontal Stripe]' };
  if (pm25 <= 250) return { label: 'Poor / Severe (121-250)', icon: '🔴', pattern: '[Crosshatch]' };
  return { label: 'Hazardous / Emergency (250+)', icon: '🟣', pattern: '[Stippled Grid]' };
}

/**
 * Update document root HTML lang attribute.
 *
 * @param {string} lang - Active language code.
 * @returns {void}
 */
export function updateDocumentLang(lang) {
  if (typeof document !== 'undefined' && document.documentElement) {
    document.documentElement.lang = lang;
  }
}
