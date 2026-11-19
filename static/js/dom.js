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
