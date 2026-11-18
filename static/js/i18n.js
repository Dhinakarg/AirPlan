/**
 * @fileoverview Internationalization dictionary and translation service for English and Hindi.
 */

/**
 * Supported localization keys and their translations.
 * @type {Record<string, {en: string, hi: string}>}
 */
const DICTIONARY = {
  siteTitle: {
    en: 'AirLedger',
    hi: 'एयरलेजर (AirLedger)',
  },
  siteTagline: {
    en: 'Household Clean-Air Exposure & Intervention Planner',
    hi: 'घरेलू स्वच्छ हवा और स्मॉग सुरक्षा योजना',
  },
  highContrast: {
    en: 'High Contrast',
    hi: 'उच्च कंट्रास्ट',
  },
  plainLanguage: {
    en: 'Plain Language',
    hi: 'सरल भाषा',
  },
  householdProfile: {
    en: 'Household Profile',
    hi: 'घर का विवरण',
  },
  cookingFuel: {
    en: 'Primary Cooking Fuel',
    hi: 'रसोई का मुख्य ईंधन',
  },
  exhaustFan: {
    en: 'Exhaust fan installed in kitchen',
    hi: 'रसोई में एग्जॉस्ट फैन मौजूद है',
  },
  incenseCoils: {
    en: 'Regular incense (agarbatti) or mosquito coils',
    hi: 'अगरबत्ती या मच्छर भगाने वाली कॉइल का उपयोग',
  },
  sealingDrafts: {
    en: 'Weatherstripped windows and draft seals',
    hi: 'खिड़कियों और दरवाजों पर सील/वेदरस्ट्रिप',
  },
  roomVolume: {
    en: 'Room Air Volume (m³)',
    hi: 'कमरे का आयतन (m³)',
  },
  purifierCadr: {
    en: 'Existing Purifier CADR (m³/h)',
    hi: 'मौजूदा एयर प्यूरीफायर CADR (m³/h)',
  },
  generatePlan: {
    en: 'Generate Clean-Air Plan',
    hi: 'स्वच्छ हवा योजना तैयार करें',
  },
  exposureReduction: {
    en: 'Exposure Reduction',
    hi: 'प्रदूषण में कुल कमी',
  },
  indoorAvg: {
    en: 'Average Indoor PM2.5 (µg/m³)',
    hi: 'औसत इनडोर PM2.5 (µg/m³)',
  },
  smogAlert: {
    en: 'Smog Alert Status',
    hi: 'स्मॉग चेतावनी स्थिति',
  },
  sourcesTitle: {
    en: 'Identified Indoor Pollution Sources',
    hi: 'पहचाने गए इनडोर प्रदूषण स्रोत',
  },
  interventionsTitle: {
    en: 'Ranked Low-Cost Interventions',
    hi: 'सस्ते और प्रभावी उपाय (किफायती क्रम में)',
  },
  timelineTitle: {
    en: '24-Hour Smog Exposure Ledger',
    hi: '24 घंटे का स्मॉग और जोखिम बहीखाता',
  },
  membersTitle: {
    en: 'Family Member Personal Plans',
    hi: 'परिवार के सदस्यों की व्यक्तिगत योजना',
  },
  loading: {
    en: 'Calculating plan...',
    hi: 'योजना तैयार की जा रही है...',
  },
};

/**
 * Retrieve localized string for key.
 * @param {string} key - Dictionary key.
 * @param {'en' | 'hi'} [lang='en'] - Target language.
 * @returns {string} Localized text.
 */
export function t(key, lang = 'en') {
  const entry = DICTIONARY[key];
  if (!entry) {
    return key;
  }
  return lang === 'hi' ? entry.hi : entry.en;
}

/**
 * Format numerical exposure with physical unit.
 * @param {number} val - Numerical concentration.
 * @returns {string} Formatted string with unit.
 */
export function formatConcentration(val) {
  return `${val.toFixed(1)} µg/m³`;
}

