# Security

Implemented and tested: PBKDF2-SHA256 passwords (200k iterations), HMAC-signed expiring tokens, per-user rate limiting, upload validation,
per-user data scoping (foreign documents look like "not found"), prompt-injection quarantine, evidence escaping, SSRF guard
(https only, host allow-list, rejects private/loopback/link-local resolutions), user-safe error messages (no stack traces).

Known gaps: rate limiting and tokens are process-local (use Redis and a rotating secret store for multi-instance); no refresh tokens or
password reset; injection detection is pattern-based and bypassable; arXiv XML is parsed with the stdlib parser (use `defusedxml` for untrusted hosts);
SSRF check resolves DNS before the request (a rebinding window remains); CORS origins come from `CORS_ORIGINS`; no audit log; no virus scanning.
