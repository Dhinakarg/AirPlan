import { test } from 'node:test';
import assert from 'node:assert/strict';

class MockEl {
  constructor(tag) {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.attrs = {};
    this.listeners = {};
    this.className = '';
    this.textContent = '';
    this.id = '';
    this.hidden = false;
  }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  addEventListener(e, fn) { (this.listeners[e] ||= []).push(fn); }
  appendChild(c) { this.children.push(c); return c; }
  append(...items) { items.forEach((c) => this.appendChild(c)); }
  replaceChildren(...items) { this.children = items; }
  querySelector(sel) {
    if (sel.startsWith('#')) {
      const id = sel.slice(1);
      if (this.id === id) return this;
      for (const c of this.children) {
        const hit = c.querySelector?.(sel);
        if (hit) return hit;
      }
    }
    return null;
  }
}

function setupMockDom() {
  const byId = {};
  globalThis.document = {
    createElement(tag) { return new MockEl(tag); },
    createElementNS(_ns, tag) { return new MockEl(tag); },
    createTextNode(t) { return new MockEl('#text', t); },
    getElementById(id) { return byId[id] || null; },
  };
  return byId;
}

import { resetState, setState } from '../../static/js/state.js';
import { switchScreen } from '../../static/js/navigation.js';
import { renderResultsScreen } from '../../static/js/render/results.js';

test('step 3 auto-generates plan on entry and reuses until inputs change', async () => {
  setupMockDom();
  resetState();
  let fetchCalls = 0;
  globalThis.fetch = async () => {
    fetchCalls += 1;
    return {
      ok: true,
      json: async () => ({
        members_exposure: { Aarav: { index: 65, hours: [] } },
        ventilation_window: { start_hour: 13, end_hour: 15, mean_pm25: 75 },
        worst_window: { start_hour: 19, end_hour: 22, mean_pm25: 290 },
        inversion: { hours: [22, 23], method: 'boundary_layer_height' },
        ranked_interventions: [],
        data_source: 'demo:moderate',
      }),
    };
  };

  switchScreen('screen-results');
  await new Promise((r) => setTimeout(r, 15));
  assert.equal(fetchCalls, 1, 'Entering step 3 must trigger plan API call');

  switchScreen('screen-results');
  await new Promise((r) => setTimeout(r, 15));
  assert.equal(fetchCalls, 1, 'Unchanged inputs should reuse existing plan');

  setState({ budgetInr: 1200 });
  switchScreen('screen-results');
  await new Promise((r) => setTimeout(r, 15));
  assert.equal(fetchCalls, 2, 'Changed inputs must regenerate plan on step 3 entry');
});

test('results screen renders aria-live skeleton while loading and Retry on error/empty', () => {
  setupMockDom();
  resetState();
  const container = new MockEl('section');

  setState({ isLoading: true });
  renderResultsScreen(container);
  const skel = container.querySelector('#plan-loading-skeleton');
  assert.ok(skel, 'Skeleton container should render during loading');
  assert.equal(skel.getAttribute('aria-live'), 'polite');

  setState({ isLoading: false, error: 'Network timeout' });
  renderResultsScreen(container);
  assert.ok(container.querySelector('#retry-plan-btn'), 'Error state must show Retry button');

  setState({ isLoading: false, error: null, planResult: null });
  renderResultsScreen(container);
  assert.ok(container.querySelector('#retry-plan-btn'), 'Empty state must show Retry button');
});
