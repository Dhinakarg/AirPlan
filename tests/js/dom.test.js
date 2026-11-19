import test from 'node:test';
import assert from 'node:assert/strict';
import { el } from '../../static/js/dom.js';

class MockNode {
  constructor(tag, cls = '', text = '') {
    this.tagName = tag.toUpperCase();
    this.className = cls;
    this.textContent = text;
    this.children = [];
    this.attributes = {};
  }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  getAttribute(k) { return this.attributes[k]; }
  appendChild(child) {
    this.children.push(child);
    return child;
  }
}

globalThis.Node = MockNode;
globalThis.document = {
  createElement: (tag) => new MockNode(tag),
  createTextNode: (text) => new MockNode('#text', '', text),
};

test('dom helper: el creates elements with class and text', () => {
  const p = el('p', 'intro text-primary', 'Welcome to AirPlan');
  assert.equal(p.tagName, 'P');
  assert.equal(p.className, 'intro text-primary');
  assert.equal(p.textContent, 'Welcome to AirPlan');
});

test('dom helper: el sets boolean and dictionary attributes safely', () => {
  const btn = el('button', {
    id: 'submit-btn',
    className: 'btn btn-primary',
    type: 'button',
    disabled: true,
    'aria-label': 'Submit Form',
  });
  assert.equal(btn.tagName, 'BUTTON');
  assert.equal(btn.className, 'btn btn-primary');
  assert.equal(btn.getAttribute('id'), 'submit-btn');
  assert.equal(btn.getAttribute('type'), 'button');
  assert.equal(btn.getAttribute('disabled'), '');
  assert.equal(btn.getAttribute('aria-label'), 'Submit Form');
});

test('dom helper: el appends nested children and array of children', () => {
  const span1 = el('span', 'badge', 'PM2.5');
  const span2 = el('span', 'val', '150');
  const container = el('div', 'row', [span1, ' - ', span2]);

  assert.equal(container.children.length, 3);
  assert.equal(container.children[0].tagName, 'SPAN');
  assert.equal(container.children[1].textContent, ' - ');
  assert.equal(container.children[2].textContent, '150');
});
