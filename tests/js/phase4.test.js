import assert from 'node:assert/strict';
import test from 'node:test';

class MockEl {
  constructor(tag) {
    this.tagName = tag.toUpperCase();
    this.className = '';
    this.textContent = '';
    this.children = [];
    this.attributes = {};
    this.listeners = {};
    this.style = {};
    this.hidden = true;
    this.tabIndex = -1;
    this.classList = {
      _set: new Set(),
      add: (cls) => this.classList._set.add(cls),
      remove: (cls) => this.classList._set.delete(cls),
      toggle: (cls, force) => {
        if (force === undefined) {
          if (this.classList._set.has(cls)) { this.classList._set.delete(cls); return false; }
          this.classList._set.add(cls); return true;
        }
        if (force) this.classList._set.add(cls); else this.classList._set.delete(cls);
        return Boolean(force);
      },
      contains: (cls) => this.classList._set.has(cls),
    };
  }
  focus() {}
  setAttribute(k, v) { this.attributes[k] = String(v); }
  getAttribute(k) { return this.attributes[k] ?? null; }
  appendChild(c) { this.children.push(c); return c; }
  append(...nodes) { nodes.forEach((n) => this.appendChild(n)); }
  addEventListener(ev, fn) { (this.listeners[ev] ||= []).push(fn); }
  dispatchEvent(ev) { (this.listeners[ev.type] || []).forEach((fn) => fn(ev)); }
}

const byId = {
  'status-announcer': new MockEl('div'),
  'error-alert': new MockEl('div'),
};
const docEl = new MockEl('html');
const store = new Map();
globalThis.Node = MockEl;
globalThis.localStorage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: (k) => store.delete(k),
};
globalThis.window = { localStorage: globalThis.localStorage };
globalThis.document = {
  documentElement: docEl,
  body: docEl,
  createElement: (tag) => new MockEl(tag),
  createTextNode: (t) => Object.assign(new MockEl('#text'), { textContent: t }),
  getElementById: (id) => byId[id] || null,
  dispatchEvent: () => true,
};

const { buildSelect } = await import('../../static/js/dom.js');
const { announce, showError, toggleHighContrast, setTextSize } = await import('../../static/js/a11y.js');
const { DICTIONARY } = await import('../../static/js/dictionary.js');
const { buildToolNav } = await import('../../static/js/render/tool_nav.js');
const { loadSavedHousehold, saveHousehold, clearSavedHousehold } = await import('../../static/js/storage.js');

test('dom.buildSelect builds options, marks selected, and fires onChange', () => {
  let picked = null;
  const sel = buildSelect('my-sel', [{ val: 'a', label: 'Alpha' }, { val: 'b', label: 'Beta' }], 'b', (v) => { picked = v; });
  assert.equal(sel.attributes.id, 'my-sel');
  assert.equal(sel.children.length, 2);
  assert.equal(sel.children[1].selected, true);
  sel.dispatchEvent({ type: 'change', target: { value: 'a' } });
  assert.equal(picked, 'a');
});

test('storage helpers save, load, and clear persisted household', () => {
  clearSavedHousehold();
  assert.equal(loadSavedHousehold(), null);
  saveHousehold({ city: 'delhi', budgetInr: 900, heroDismissed: true, members: [{ name: 'Aarav' }] });
  const loaded = loadSavedHousehold();
  assert.equal(loaded.city, 'delhi');
  assert.equal(loaded.budgetInr, 900);
  clearSavedHousehold();
  assert.equal(loadSavedHousehold(), null);
});

test('a11y helpers update live region, error banner, contrast, and text size', async () => {
  announce('Plan ready', 'assertive');
  assert.equal(byId['status-announcer'].getAttribute('aria-live'), 'assertive');
  await new Promise((r) => setTimeout(r, 70));
  assert.equal(byId['status-announcer'].textContent, 'Plan ready');
  showError('Network down');
  assert.equal(byId['error-alert'].classList.contains('sr-only'), false);
  assert.equal(byId['error-alert'].textContent, 'Network down');
  assert.equal(toggleHighContrast(true), true);
  assert.equal(docEl.classList.contains('high-contrast'), true);
  setTextSize('large');
  assert.equal(docEl.style.fontSize, '115%');
});

test('tool_nav renders back button and active tool tab', () => {
  const nav = buildToolNav('screen-detective', 'en');
  assert.equal(nav.children[0].textContent.includes('Clean-Air Plan'), true);
  const links = nav.children[1].children;
  assert.equal(links.length, 3);
  assert.equal(links[0].getAttribute('aria-current'), 'page');
  assert.equal(links[1].getAttribute('aria-current'), null);
});

test('all dictionary keys are non-empty in both English and Hindi', () => {
  for (const [key, entry] of Object.entries(DICTIONARY)) {
    assert.ok(entry.en && entry.en.trim().length > 0, `Missing en for ${key}`);
    assert.ok(entry.hi && entry.hi.trim().length > 0, `Missing hi for ${key}`);
  }
});
