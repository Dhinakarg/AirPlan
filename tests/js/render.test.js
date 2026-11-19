import test from 'node:test';
import assert from 'node:assert/strict';
import { getAqiCategory, formatConcentration, labelFor } from '../../static/js/i18n.js';
import { PRESET_CITIES, DEFAULT_ROUTINE } from '../../static/js/state.js';

test('render helpers: formatConcentration formats valid float strings', () => {
  assert.equal(formatConcentration(45.2), '45.2 µg/m³');
  assert.equal(formatConcentration(300), '300.0 µg/m³');
  assert.equal(formatConcentration(0), '0.0 µg/m³');
  assert.equal(formatConcentration(12.3456), '12.3 µg/m³');
});

test('render helpers: getAqiCategory covers all standard particulate ranges and thresholds', () => {
  const boundaryTests = [
    { pm25: 15, icon: '🟢', pattern: '[Solid Dot]' },
    { pm25: 45, icon: '🟡', pattern: '[Diagonal Slash]' },
    { pm25: 80, icon: '🟠', pattern: '[Horizontal Stripe]' },
    { pm25: 180, icon: '🔴', pattern: '[Crosshatch]' },
    { pm25: 350, icon: '🟣', pattern: '[Stippled Grid]' },
  ];

  boundaryTests.forEach(({ pm25, icon, pattern }) => {
    const res = getAqiCategory(pm25);
    assert.equal(res.icon, icon);
    assert.equal(res.pattern, pattern);
    assert.ok(res.label.length > 0);
  });
});

test('render helpers: labelFor maps all domain enums cleanly in en and hi', () => {
  assert.equal(labelFor('ageGroup', 'child', 'en'), 'Child');
  assert.equal(labelFor('ageGroup', 'toddler', 'hi'), 'टॉडलर');
  assert.equal(labelFor('sensitivity', 'asthma_or_heart', 'en'), 'Asthma or heart condition');
  assert.equal(labelFor('cookingFuel', 'wood', 'en'), 'Firewood');
  assert.equal(labelFor('kitchenExhaust', 'vented', 'en'), 'Vented chimney to outside');
  assert.equal(labelFor('sweeping', 'wet', 'en'), 'Wet mopping');
  assert.equal(labelFor('mode', 'metro', 'en'), 'Metro train');
  assert.equal(labelFor('activity', 'sleep', 'en'), 'Sleeping');
  // Unknown group or key fallback
  assert.equal(labelFor('unknown_group', 'custom_key', 'en'), 'custom_key');
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

