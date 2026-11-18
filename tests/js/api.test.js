import test from 'node:test';
import assert from 'node:assert/strict';
import {
  fetchHealth,
  createPlan,
  simulateRoutine,
  analyzeHome,
  submitPledge,
  fetchCommunitySummary,
  askAssistant,
} from '../../static/js/api.js';

test('api: fetchHealth calls GET /api/v1/health with tracking header', async () => {
  const originalFetch = globalThis.fetch;
  let requestedUrl = '';
  let requestedHeaders = null;

  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestedHeaders = options.headers;
    return {
      ok: true,
      json: async () => ({ status: 'ok' }),
    };
  };

  try {
    const res = await fetchHealth();
    assert.equal(requestedUrl, '/api/v1/health');
    assert.ok(requestedHeaders['X-Correlation-ID'].startsWith('web-'));
    assert.equal(res.status, 'ok');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('api: createPlan sends POST /api/v1/plan with JSON payload', async () => {
  const originalFetch = globalThis.fetch;
  let method = '';
  let body = '';

  globalThis.fetch = async (url, options) => {
    method = options.method;
    body = JSON.parse(options.body);
    return {
      ok: true,
      json: async () => ({ data_source: 'sample', members_exposure: {} }),
    };
  };

  try {
    const res = await createPlan({ budget_inr: 500 });
    assert.equal(method, 'POST');
    assert.equal(body.budget_inr, 500);
    assert.equal(res.data_source, 'sample');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('api: error mapping extracts domain error from JSON response', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 422,
    json: async () => ({ error: 'Payload validation rejected: extra fields' }),
  });

  try {
    await assert.rejects(
      async () => {
        await createPlan({});
      },
      {
        name: 'Error',
        message: 'Payload validation rejected: extra fields',
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('api: error mapping falls back to HTTP status when body is non-JSON', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 502,
    json: async () => {
      throw new Error('Invalid JSON');
    },
  });

  try {
    await assert.rejects(
      async () => {
        await fetchCommunitySummary('DL-01');
      },
      {
        name: 'Error',
        message: 'HTTP 502: Request failed',
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('api: askAssistant sends question facts and language', async () => {
  const originalFetch = globalThis.fetch;
  let sentPayload = null;

  globalThis.fetch = async (url, options) => {
    sentPayload = JSON.parse(options.body);
    return {
      ok: true,
      json: async () => ({ summary: 'OK', tips: [], answer: 'Done', is_red_flag: false }),
    };
  };

  try {
    const res = await askAssistant('Safe window?', { window_start: 13 }, 'en');
    assert.equal(sentPayload.question, 'Safe window?');
    assert.equal(sentPayload.facts.window_start, 13);
    assert.equal(res.summary, 'OK');
  } finally {
    globalThis.fetch = originalFetch;
  }
});
