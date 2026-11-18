import test from 'node:test';
import assert from 'node:assert/strict';

test('frontend smoke test: verify state module initializes cleanly', async () => {
  const stateModule = await import('../../static/js/state.js');
  assert.equal(typeof stateModule.getState, 'function');
  const initialState = stateModule.getState();
  assert.equal(typeof initialState, 'object');
  assert.equal(initialState.language, 'en');
});

test('frontend smoke test: verify i18n dictionary functions', async () => {
  const i18nModule = await import('../../static/js/i18n.js');
  assert.equal(typeof i18nModule.t, 'function');
  assert.equal(i18nModule.t('siteTitle', 'en'), 'AirPlan');
});

