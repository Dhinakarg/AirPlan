/**
 * @fileoverview Pure DOM construction utilities using strict native APIs.
 */

/**
 * Create a DOM element with optional classes/attributes and children.
 * Uses only document.createElement and textContent for safety against injection.
 *
 * @param {string} tag - HTML tag name.
 * @param {string | Record<string, string | number | boolean>} [attrs=''] - Class name string or attribute dictionary.
 * @param {string | Node | (string | Node)[]} [children=''] - Text content or child nodes.
 * @returns {HTMLElement} Newly constructed DOM element.
 */
export function el(tag, attrs = '', children = '') {
  const node = document.createElement(tag);
  if (typeof attrs === 'string') {
    if (attrs) node.className = attrs;
  } else if (attrs && typeof attrs === 'object') {
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'className' || k === 'class') {
        node.className = String(v);
      } else if (v === true) {
        node.setAttribute(k, '');
      } else if (v !== false && v != null) {
        node.setAttribute(k, String(v));
      }
    }
  }

  if (typeof children === 'string' || typeof children === 'number') {
    if (children !== '') node.textContent = String(children);
  } else if (children instanceof Node) {
    node.appendChild(children);
  } else if (Array.isArray(children)) {
    for (const child of children) {
      if (typeof child === 'string' || typeof child === 'number') {
        node.appendChild(document.createTextNode(String(child)));
      } else if (child instanceof Node) {
        node.appendChild(child);
      }
    }
  }
  return node;
}

/**
 * Build a <select> element from option descriptors with an optional change handler.
 *
 * @param {string | Record<string, string | number | boolean>} attrs - Element id string or attribute dictionary.
 * @param {Array<string | {val?: string, value?: string, id?: string, label: string, disabled?: boolean}>} options - Option items.
 * @param {string | number} [currentVal=''] - Initially selected option value.
 * @param {(val: string) => void} [onChange] - Optional change callback receiving the selected value.
 * @returns {HTMLSelectElement} Constructed select element.
 */
export function buildSelect(attrs, options, currentVal = '', onChange) {
  const sel = /** @type {HTMLSelectElement} */ (el('select', typeof attrs === 'string' ? { id: attrs } : attrs));
  options.forEach((o) => {
    const val = typeof o === 'object' ? String(o.val ?? o.value ?? o.id ?? '') : String(o);
    const text = typeof o === 'object' ? o.label : String(o);
    const opt = Object.assign(document.createElement('option'), {
      value: val,
      textContent: text,
      selected: val === String(currentVal),
      disabled: Boolean(typeof o === 'object' && o.disabled),
    });
    sel.appendChild(opt);
  });
  if (onChange) sel.addEventListener('change', (e) => onChange(e.target.value));
  return sel;
}
