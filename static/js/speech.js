/**
 * @fileoverview Web Speech API utilities for browser speech synthesis.
 */

/**
 * Check if Web Speech API is supported.
 * @returns {boolean} True if speech synthesis is available.
 */
export function isSpeechSupported() {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
}

/**
 * Speak text aloud using speechSynthesis.
 * @param {string} text - Text to synthesize.
 * @param {'en' | 'hi'} [lang='en'] - Spoken language.
 * @returns {void}
 */
export function speakText(text, lang = 'en') {
  if (!isSpeechSupported() || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-US';
  window.speechSynthesis.speak(utterance);
}

/**
 * Cancel active speech synthesis.
 * @returns {void}
 */
export function stopSpeaking() {
  if (isSpeechSupported()) window.speechSynthesis.cancel();
}

