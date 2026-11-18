import test from 'node:test';
import assert from 'node:assert/strict';
import { getAqiCategory, formatConcentration } from '../../static/js/i18n.js';
import { PRESET_CITIES, DEFAULT_ROUTINE } from '../../static/js/state.js';

test('render helpers: formatConcentration formats valid float strings', () => {
  assert.equal(formatConcentration(45.2), '45.2 µg/m³');
  assert.equal(formatConcentration(300), '300.0 µg/m³');
});

test('render helpers: getAqiCategory covers all standard particulate ranges', () => {
  const levels = [15, 45, 90, 180, 400];
  const results = levels.map((l) => getAqiCategory(l));
  assert.equal(results.length, 5);
  results.forEach((r) => {
    assert.ok(r.label.length > 0);
    assert.ok(r.icon.length > 0);
    assert.ok(r.pattern.startsWith('['));
    assert.ok(r.pattern.endsWith(']'));
  });
});

test('render helpers: PRESET_CITIES contains valid latitudes and longitudes', () => {
  const cityKeys = Object.keys(PRESET_CITIES);
  assert.equal(cityKeys.length, 5);
  cityKeys.forEach((k) => {
    const c = PRESET_CITIES[k];
    assert.ok(c.lat >= -90 && c.lat <= 90);
    assert.ok(c.lon >= -180 && c.lon <= 180);
    assert.ok(c.name.length > 0);
  });
});

test('render helpers: DEFAULT_ROUTINE covers complete 24-hour cycle without gaps', () => {
  let prevEnd = 0;
  DEFAULT_ROUTINE.forEach((block) => {
    assert.equal(block.start_hour, prevEnd);
    assert.ok(block.end_hour > block.start_hour);
    prevEnd = block.end_hour;
  });
  assert.equal(prevEnd, 24);
});
