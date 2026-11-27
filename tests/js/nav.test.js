import { test } from 'node:test';
import assert from 'node:assert/strict';

class NavMockEl {
  constructor(id) {
    this.id = id;
    this.attrs = {};
    this.listeners = {};
    this.hidden = false;
  }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  removeAttribute(k) { delete this.attrs[k]; }
  addEventListener(e, fn) { (this.listeners[e] ||= []).push(fn); }
  focus() {}
}

import { resetState } from '../../static/js/state.js';
import { bindHeaderControls, switchScreen } from '../../static/js/navigation.js';

test('stepper tracks done, current, and upcoming states across screens', () => {
  const byId = {
    'step-btn-1': new NavMockEl('step-btn-1'),
    'step-btn-2': new NavMockEl('step-btn-2'),
    'step-btn-3': new NavMockEl('step-btn-3'),
    'screen-family': new NavMockEl('screen-family'),
    'screen-ledger': new NavMockEl('screen-ledger'),
    'screen-results': new NavMockEl('screen-results'),
    'hero-banner': new NavMockEl('hero-banner'),
    'hero-setup-btn': new NavMockEl('hero-setup-btn'),
  };
  globalThis.document = {
    getElementById(id) { return byId[id] || null; },
    addEventListener() {},
  };
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ members_exposure: {}, ranked_interventions: [], data_source: 'sample' }) });

  resetState();
  bindHeaderControls(() => {});
  assert.equal(byId['hero-banner'].hidden, false);

  switchScreen('screen-ledger');
  assert.equal(byId['step-btn-1'].getAttribute('data-state'), 'done');
  assert.equal(byId['step-btn-2'].getAttribute('data-state'), 'current');
  assert.equal(byId['step-btn-2'].getAttribute('aria-current'), 'step');
  assert.equal(byId['step-btn-3'].getAttribute('data-state'), 'upcoming');

  switchScreen('screen-results');
  assert.equal(byId['step-btn-1'].getAttribute('data-state'), 'done');
  assert.equal(byId['step-btn-2'].getAttribute('data-state'), 'done');
  assert.equal(byId['step-btn-3'].getAttribute('data-state'), 'current');
});
