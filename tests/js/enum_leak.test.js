import test from 'node:test';
import assert from 'node:assert/strict';
import { labelFor } from '../../static/js/i18n.js';
import { renderFamilyScreen } from '../../static/js/render/family.js';
import { getState, setState, resetState } from '../../static/js/state.js';

class MockElement {
  constructor(tag, cls = '', text = '') {
    this.tagName = tag.toUpperCase();
    this.className = cls;
    this.textContent = text;
    this.children = [];
    this.attributes = {};
    this.style = {};
  }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  getAttribute(k) { return this.attributes[k]; }
  removeAttribute(k) { delete this.attributes[k]; }
  appendChild(child) {
    if (child) this.children.push(child);
    return child;
  }
  append(...items) {
    items.forEach((item) => {
      if (typeof item === 'string') this.textContent += item;
      else if (item && typeof item === 'object') this.children.push(item);
    });
  }
  prepend(...items) {
    items.reverse().forEach((item) => {
      if (typeof item === 'string') this.textContent = item + this.textContent;
      else if (item && typeof item === 'object') this.children.unshift(item);
    });
  }
  replaceChildren(...items) {
    this.children = [];
    this.textContent = '';
    this.append(...items);
  }
  addEventListener() {}
  getAllText() {
    let txt = this.textContent || '';
    for (const c of this.children) {
      if (c && c.getAllText) txt += ' ' + c.getAllText();
    }
    return txt;
  }
  findChildrenByTag(tag) {
    const res = [];
    for (const c of this.children) {
      if (c && c.tagName === tag.toUpperCase()) res.push(c);
      if (c && c.findChildrenByTag) res.push(...c.findChildrenByTag(tag));
    }
    return res;
  }
}

test('labelFor helper: resolves display labels without raw underscore enum keys', () => {
  const groupsAndValues = [
    ['ageGroup', 'child', 'Child'],
    ['ageGroup', 'toddler', 'Toddler'],
    ['ageGroup', 'adult', 'Adult'],
    ['sensitivity', 'asthma_or_heart', 'Asthma or heart condition'],
    ['sensitivity', 'none', 'Standard health'],
    ['leakiness', 'tight', 'Tight'],
    ['leakiness', 'average', 'Average'],
    ['leakiness', 'leaky', 'Leaky (Draughty)'],
    ['activity', 'exercise', 'Vigorous exercise'],
    ['mode', 'auto_rickshaw', 'Auto rickshaw'],
    ['cookingFuel', 'electric_coil', 'Electric coil stove'],
  ];

  for (const [group, val, expected] of groupsAndValues) {
    const label = labelFor(group, val, 'en');
    assert.equal(label, expected, `labelFor(${group}, ${val}) should match '${expected}'`);
    assert.doesNotMatch(label, /_/, `Rendered label '${label}' must never contain underscores`);
  }
});

test('enum leaks: rendered Family & Home screen never displays underscore-separated enum keys', () => {
  globalThis.document = {
    createElement(tag) { return new MockElement(tag); },
    createTextNode(text) { return new MockElement('span', '', text); },
  };

  resetState();
  setState({
    members: [
      { name: 'Aarav', age_group: 'child', sensitivity: 'asthma_or_heart', routine: [] },
      { name: 'Sunita', age_group: 'adult', sensitivity: 'none', routine: [] },
    ],
  });

  const container = new MockElement('div');
  renderFamilyScreen(container);

  const fullText = container.getAllText();

  // 1. Must specifically render name on line one and "Child · Asthma or heart condition" on line two
  assert.ok(
    fullText.includes('Aarav') && fullText.includes('Child · Asthma or heart condition'),
    'Member card must render "Aarav" and line two "Child · Asthma or heart condition"'
  );

  // 2. Must not render "[child, asthma_or_heart]"
  assert.ok(!fullText.includes('[child, asthma_or_heart]'));

  // 3. Must never display any raw underscore-separated enum key in visible text
  const underscoreMatches = fullText.match(/\b[a-z]+_[a-z]+\b/g) || [];
  assert.deepEqual(
    underscoreMatches,
    [],
    `Found leaked raw enum keys in rendered text: ${underscoreMatches.join(', ')}`
  );

  // 4. Select options must have labels without underscores while values keep enum keys
  const options = container.findChildrenByTag('option');
  assert.ok(options.length > 0, 'Should render select options');
  options.forEach((opt) => {
    assert.doesNotMatch(
      opt.textContent || '',
      /_/,
      `Option text '${opt.textContent}' must not contain underscores`
    );
  });
});
