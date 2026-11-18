import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { DICTIONARY, t, formatConcentration, getAqiCategory, updateDocumentLang } from '../../static/js/i18n.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('i18n: full key parity between en.json and hi.json', () => {
  const enPath = path.resolve(__dirname, '../../static/i18n/en.json');
  const hiPath = path.resolve(__dirname, '../../static/i18n/hi.json');

  const enKeys = Object.keys(JSON.parse(fs.readFileSync(enPath, 'utf-8'))).sort();
  const hiKeys = Object.keys(JSON.parse(fs.readFileSync(hiPath, 'utf-8'))).sort();

  assert.deepEqual(enKeys, hiKeys, 'en.json and hi.json must have identical keys');
});

test('i18n: full key parity between en.json and JS DICTIONARY', () => {
  const enPath = path.resolve(__dirname, '../../static/i18n/en.json');
  const enKeys = Object.keys(JSON.parse(fs.readFileSync(enPath, 'utf-8'))).sort();
  const dictKeys = Object.keys(DICTIONARY).sort();

  assert.deepEqual(enKeys, dictKeys, 'en.json and i18n.js DICTIONARY must have identical keys');
});

test('i18n: t() returns correct translation and falls back to key when missing', () => {
  assert.equal(t('siteTitle', 'en'), 'AirPlan');
  assert.match(t('siteTitle', 'hi'), /एयरप्लान/);
  assert.equal(t('nonexistent_key', 'en'), 'nonexistent_key');
});

test('i18n: formatConcentration outputs rounded value with physical unit', () => {
  assert.equal(formatConcentration(123.456), '123.5 µg/m³');
  assert.equal(formatConcentration(0), '0.0 µg/m³');
});

test('i18n: getAqiCategory returns multi-attribute classification with label, icon, and pattern', () => {
  const good = getAqiCategory(25);
  assert.equal(good.icon, '🟢');
  assert.match(good.label, /Good/);
  assert.equal(good.pattern, '[Solid Dot]');

  const mod = getAqiCategory(80);
  assert.equal(mod.icon, '🟠');
  assert.match(mod.label, /Moderate/);
  assert.equal(mod.pattern, '[Horizontal Stripe]');

  const severe = getAqiCategory(200);
  assert.equal(severe.icon, '🔴');
  assert.match(severe.label, /Severe/);
  assert.equal(severe.pattern, '[Crosshatch]');

  const haz = getAqiCategory(350);
  assert.equal(haz.icon, '🟣');
  assert.match(haz.label, /Hazardous/);
  assert.equal(haz.pattern, '[Stippled Grid]');
});

test('i18n: updateDocumentLang handles environment gracefully', () => {
  assert.doesNotThrow(() => {
    updateDocumentLang('hi');
  });
});

