/**
 * @fileoverview Safe DOM manipulation utilities adhering strictly to textContent and createElement.
 * Never uses innerHTML or eval.
 */

/**
 * Clear all child nodes from a DOM container.
 * @param {HTMLElement} element - Target element.
 * @returns {void}
 */
export function clearElement(element) {
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
}

/**
 * Create a DOM text node.
 * @param {string | number} content - Text content.
 * @returns {Text} Text node instance.
 */
export function text(content) {
  return document.createTextNode(String(content));
}

/**
 * Create an element with attributes, class names, and children safely without innerHTML.
 * @param {string} tag - HTML tag name.
 * @param {Record<string, string | boolean | function(Event): void>} [attributes={}] - Attributes.
 * @param {...(Node | string | number | null | undefined)} children - Child nodes or text strings.
 * @returns {HTMLElement} Newly created element.
 */
export function el(tag, attributes = {}, ...children) {
  const element = document.createElement(tag);

  for (const [key, value] of Object.entries(attributes)) {
    if (value === null || value === undefined) {
      continue;
    }
    if (key.startsWith('on') && typeof value === 'function') {
      const eventName = key.substring(2).toLowerCase();
      element.addEventListener(eventName, value);
    } else if (typeof value === 'boolean') {
      if (value) {
        element.setAttribute(key, '');
      }
    } else {
      element.setAttribute(key, String(value));
    }
  }

  for (const child of children) {
    if (child === null || child === undefined) {
      continue;
    }
    if (child instanceof Node) {
      element.appendChild(child);
    } else {
      element.appendChild(text(child));
    }
  }

  return element;
}

/**
 * Create an accessible status badge element.
 * @param {string} label - Display label.
 * @param {'high' | 'medium' | 'low' | 'neutral'} [severity='neutral'] - Visual indicator style.
 * @returns {HTMLElement} Badge span element.
 */
export function makeBadge(label, severity = 'neutral') {
  const badgeClass = severity !== 'neutral' ? `badge badge-${severity}` : 'badge';
  return el('span', { class: badgeClass }, label);
}

