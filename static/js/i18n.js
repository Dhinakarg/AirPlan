/**
 * @fileoverview Internationalization dictionary and translation service for English and Hindi.
 */

/** @type {Record<string, {en: string, hi: string}>} */
export const DICTIONARY = {
  siteTitle: { en: 'AirLedger', hi: 'एयरलेजर (AirLedger)' },
  siteTagline: {
    en: 'Household Clean-Air Exposure & Intervention Planner',
    hi: 'घरेलू स्वच्छ हवा और स्मॉग सुरक्षा योजना',
  },
  skipLink: { en: 'Skip to main content', hi: 'मुख्य सामग्री पर जाएं' },
  demoDataBanner: {
    en: 'Demo data (Offline winter smog sample)',
    hi: 'डेमो डेटा (ऑफ़लाइन स्मॉग नमूना)',
  },
  language: { en: 'Language', hi: 'भाषा' },
  highContrast: { en: 'High Contrast', hi: 'उच्च कंट्रास्ट' },
  plainLanguage: { en: 'Plain Language', hi: 'सरल भाषा' },
  textSize: { en: 'Text Size', hi: 'अक्षर का आकार' },
  readAloud: { en: 'Read Aloud', hi: 'बोलकर सुनाएं' },
  stopReadAloud: { en: 'Stop Reading', hi: 'पढ़ना बंद करें' },
  navFamily: { en: 'Family & Home', hi: 'परिवार व घर' },
  navLedger: { en: 'Day Ledger', hi: 'दिनचर्या बहीखाता' },
  navResults: { en: 'Clean-Air Plan', hi: 'स्वच्छ हवा योजना' },
  navDetective: { en: 'Home Detective', hi: 'घर का जासूस' },
  navNeighbourhood: { en: 'Neighbourhood', hi: 'पड़ोस व समुदाय' },
  navAssistant: { en: 'Ask AirLedger', hi: 'एयरलेजर से पूछें' },
  familyTitle: { en: 'Family & Household Setup', hi: 'परिवार और घर की बनावट' },
  addMember: { en: 'Add Member', hi: 'सदस्य जोड़ें' },
  removeMember: { en: 'Remove', hi: 'हटाएं' },
  memberName: { en: 'Member Name', hi: 'सदस्य का नाम' },
  ageGroup: { en: 'Age Group', hi: 'आयु वर्ग' },
  sensitivity: { en: 'Vulnerability', hi: 'स्वास्थ्य संवेदनशीलता' },
  leakiness: { en: 'Envelope Leakiness', hi: 'घर का खुलापन / रिसाव' },
  purifier: { en: 'Air Purifier Present', hi: 'एयर प्यूरीफायर मौजूद है' },
  windowsOpen: { en: 'Windows Open Hours', hi: 'खिड़की खुली रखने का समय' },
  cityPreset: { en: 'City Location', hi: 'शहर का स्थान' },
  latitude: { en: 'Latitude', hi: 'अक्षांश (Latitude)' },
  longitude: { en: 'Longitude', hi: 'देशांतर (Longitude)' },
  budgetInr: { en: 'Monthly Clean-Air Budget (INR)', hi: 'मासिक स्वच्छ-हवा बजट (रुपये)' },
  ledgerTitle: { en: 'Daily Routine Ledger', hi: 'दैनिक दिनचर्या बहीखाता' },
  startHour: { en: 'Start Hour', hi: 'शुरुआती घंटा' },
  endHour: { en: 'End Hour', hi: 'समाप्ति घंटा' },
  activity: { en: 'Activity', hi: 'गतिविधि' },
  mode: { en: 'Location / Transit Mode', hi: 'स्थान / आवागमन साधन' },
  addBlock: { en: 'Add Schedule Block', hi: 'समय खंड जोड़ें' },
  suggestBetterDay: { en: 'Suggest a Better Day', hi: 'बेहतर दिनचर्या का सुझाव' },
  generatePlan: { en: 'Generate Clean-Air Plan', hi: 'स्वच्छ हवा योजना तैयार करें' },
  resultsTitle: { en: 'Plan Results & Exposure Ledger', hi: 'योजना परिणाम और जोखिम बहीखाता' },
  exposureBefore: { en: 'Baseline Exposure Index', hi: 'प्रारंभिक जोखिम सूचकांक' },
  exposureAfter: { en: 'Mitigated Exposure Index', hi: 'घटा हुआ जोखिम सूचकांक' },
  illustrative: { en: 'illustrative', hi: 'संकेतक' },
  doseSaved: { en: 'PM2.5 Inhaled Dose Saved', hi: 'बचाई गई PM2.5 मात्रा' },
  timelineChart: {
    en: '24-Hour Particulate Exposure Timeline',
    hi: '24 घंटे का प्रदूषण जोखिम चार्ट',
  },
  ventilationWindow: {
    en: 'Ventilation Window',
    hi: 'खिड़की खोलने का सुरक्षित समय',
  },
  rankedInterventions: {
    en: 'Ranked Interventions',
    hi: 'किफायती सुरक्षा उपाय (वरीयता क्रम)',
  },
  impactReceipt: { en: 'Impact Receipt', hi: 'प्रभाव रसीद (Impact Receipt)' },
  costPerMonth: { en: 'Cost / month', hi: 'खर्च / महीना' },
  assumptions: { en: 'Assumptions', hi: 'वैज्ञानिक मान्यताएं' },
  confidence: { en: 'Confidence', hi: 'विश्वसनीयता' },
  detectiveTitle: { en: 'Home Pollution Detective', hi: 'घरेलू प्रदूषण जासूस' },
  analyzeSources: { en: 'Diagnose Indoor Sources', hi: 'इनडोर स्रोतों की जांच करें' },
  cookingFuel: { en: 'Cooking Fuel', hi: 'रसोई का ईंधन' },
  kitchenExhaust: { en: 'Kitchen Exhaust', hi: 'रसोई का एग्जॉस्ट फैन' },
  incense: { en: 'Incense / Agarbatti', hi: 'अगरबत्ती / धूप' },
  mosquitoCoil: { en: 'Mosquito Coils', hi: 'मच्छर कॉइल' },
  smokers: { en: 'Indoor Smokers', hi: 'घर में धूम्रपान' },
  pets: { en: 'Pets', hi: 'पालतू जानवर' },
  sweeping: { en: 'Sweeping Method', hi: 'सफाई का तरीका' },
  indoorReading: {
    en: 'Indoor PM2.5 Reading (µg/m³, optional)',
    hi: 'इनडोर PM2.5 माप (µg/m³, वैकल्पिक)',
  },
  suspected: { en: 'Suspected', hi: 'संदिग्ध' },
  measured: { en: 'Measured', hi: 'सत्यापित' },
  neighbourhoodTitle: {
    en: 'Neighbourhood Collective Action',
    hi: 'सामूहिक सामुदायिक पहल',
  },
  areaCode: { en: 'Area / District Code', hi: 'क्षेत्र / जिला कोड' },
  pledgeAction: { en: 'Pledge Action', hi: 'संकल्प का प्रकार' },
  pledgeCount: { en: 'Days / Trips Pledged', hi: 'संकल्प के दिन / यात्राएं' },
  submitPledge: { en: 'Submit Community Pledge', hi: 'सामुदायिक संकल्प दर्ज करें' },
  co2Card: { en: 'Emissions & Trips Avoided', hi: 'कार्बन उत्सर्जन व बचाई यात्राएं' },
  pm25Card: { en: 'Neighbourhood Air Quality Impact', hi: 'पड़ोस में वायु गुणवत्ता प्रभाव' },
  assistantTitle: {
    en: 'Ask AirLedger Clean-Air Assistant',
    hi: 'स्मॉग सुरक्षा सहायक से पूछें',
  },
  askQuestion: {
    en: 'Ask a question about smog protection (max 300 chars)',
    hi: 'वायु गुणवत्ता या सुरक्षा पर प्रश्न पूछें (अधिकतम 300 अक्षर)',
  },
  askButton: { en: 'Ask Assistant', hi: 'सहायक से पूछें' },
  emergencyAlert: {
    en: 'MEDICAL EMERGENCY ALERT',
    hi: 'आपातकालीन चिकित्सा चेतावनी',
  },
  loading: {
    en: 'Calculating clean-air plan...',
    hi: 'स्वच्छ हवा योजना तैयार हो रही है...',
  },
  ready: { en: 'Ready.', hi: 'तैयार।' },
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
  return `${Number(val).toFixed(1)} µg/m³`;
}

/**
 * Return accessible multi-attribute AQI category indicator (label + icon + pattern).
 * @param {number} pm25 - Particulate concentration in µg/m³.
 * @returns {{label: string, icon: string, pattern: string}} AQI categorization.
 */
export function getAqiCategory(pm25) {
  if (pm25 <= 30) {
    return { label: 'Good (0-30)', icon: '🟢', pattern: '[Solid Dot]' };
  }
  if (pm25 <= 60) {
    return { label: 'Satisfactory (31-60)', icon: '🟡', pattern: '[Diagonal Slash]' };
  }
  if (pm25 <= 120) {
    return { label: 'Moderate (61-120)', icon: '🟠', pattern: '[Horizontal Stripe]' };
  }
  if (pm25 <= 250) {
    return { label: 'Poor / Severe (121-250)', icon: '🔴', pattern: '[Crosshatch]' };
  }
  return { label: 'Hazardous / Emergency (250+)', icon: '🟣', pattern: '[Stippled Grid]' };
}

/**
 * Update HTML lang attribute on document root.
 * @param {'en' | 'hi'} lang - Language code.
 * @returns {void}
 */
export function updateDocumentLang(lang) {
  if (typeof document !== 'undefined' && document.documentElement) {
    document.documentElement.lang = lang;
  }
}
