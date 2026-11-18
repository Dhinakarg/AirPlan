/**
 * @fileoverview Domain and client constants for AirPlan frontend application.
 */

export const DEFAULT_COORDINATES = Object.freeze({
  latitude: 28.6139,
  longitude: 77.2090,
  city: 'Delhi',
});

export const API_ENDPOINTS = Object.freeze({
  HEALTH: '/api/v1/health',
  PLAN: '/api/v1/plan',
  SIMULATE: '/api/v1/simulate',
  HOME_ANALYZE: '/api/v1/home/analyze',
  COMMUNITY_PLEDGES: '/api/v1/community/pledges',
  COMMUNITY_SUMMARY: '/api/v1/community/summary',
  ASK: '/api/v1/ask',
});

export const AQI_THRESHOLDS = Object.freeze({
  GOOD: 30,
  MODERATE: 60,
  POOR: 120,
  VERY_POOR: 250,
});

export const MAX_MEMBERS = 6;
export const DEFAULT_BUDGET_INR = 500;
