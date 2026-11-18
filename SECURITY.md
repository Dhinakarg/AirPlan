# Security Policy

## Reporting Security Issues

Please do not report security vulnerabilities through public GitHub issues. Instead, report potential vulnerabilities privately to the maintainers at `security@airledger.local`.

---

## Security Guarantees & Defenses

1. **Strict Content Security Policy (CSP)**:
   - `default-src 'self'`
   - `script-src 'self'` (no inline scripts or eval)
   - `style-src 'self'` (no inline styles)
   - `frame-ancestors 'none'`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`

2. **Input Validation & Sanitization**:
   - Every incoming payload is validated against strict Pydantic schemas with defined bounds.
   - All user-supplied text strings are treated as untrusted data, never instructions. Prompt injection vectors are neutralized before AI model invocation.

3. **Privacy Preservation**:
   - Geographic coordinates are automatically rounded to 2 decimal places ($\approx 1.1\,\text{km}$) prior to processing or logging.
   - No user free-text or precise locations are persisted in unredacted application logs.

4. **Resource Protection & Rate Limiting**:
   - In-memory sliding-window rate limiting prevents denial-of-service abuse per client IP.
   - Generic JSON error envelopes with unique `correlation_id` values prevent stack trace leaks.
