import test from 'node:test';
import assert from 'node:assert/strict';
import { getState, setState, subscribe, resetState, PRESET_CITIES, DEFAULT_ROUTINE } from '../../static/js/state.js';

test('state: initial state has expected structure and defaults', () => {
  resetState();
  const s = getState();
  assert.equal(s.language, 'en');
  assert.equal(s.highContrast, false);
  assert.equal(s.simpleLanguage, false);
  assert.equal(s.budgetInr, 500);
  assert.equal(s.city, 'delhi');
  assert.equal(s.latitude, 28.61);
  assert.equal(s.longitude, 77.21);
  assert.equal(s.members.length, 2);
  assert.equal(typeof PRESET_CITIES.delhi, 'object');
  assert.equal(DEFAULT_ROUTINE.length, 7);
});

test('state: setState updates properties and notifies subscribers', () => {
  resetState();
  let callCount = 0;
  let receivedState = null;

  const unsubscribe = subscribe((updated) => {
    callCount++;
    receivedState = updated;
  });

  setState({ budgetInr: 1200, city: 'lucknow' });
  assert.equal(callCount, 1);
  assert.equal(receivedState.budgetInr, 1200);
  assert.equal(receivedState.city, 'lucknow');
  assert.equal(getState().budgetInr, 1200);

  unsubscribe();
  setState({ budgetInr: 2000 });
  assert.equal(callCount, 1); // Unsubscribed, count unchanged
});

test('state: subscriber error does not break other subscribers', () => {
  resetState();
  let secondReceived = false;

  const unsub1 = subscribe(() => {
    throw new Error('Exploding listener');
  });
  const unsub2 = subscribe(() => {
    secondReceived = true;
  });

  assert.doesNotThrow(() => {
    setState({ highContrast: true });
  });
  assert.equal(secondReceived, true);

  unsub1();
  unsub2();
});

test('state: resetState restores initial values', () => {
  setState({ budgetInr: 9999, language: 'hi' });
  assert.equal(getState().budgetInr, 9999);
  resetState();
  assert.equal(getState().budgetInr, 500);
  assert.equal(getState().language, 'en');
});
