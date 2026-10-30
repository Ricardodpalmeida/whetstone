# Security

Use for outside input, authentication/authorisation, sessions, secrets, cryptography, outbound calls, files and personal data. Also see [threat-modeling.md](threat-modeling.md), [supply-chain.md](supply-chain.md) for dependencies/pipelines, and [ai-features.md](ai-features.md) for model risks.

## Contents

- [Baseline for every change](#baseline-for-every-change)
- [Map the change to the OWASP Top 10](#map-the-change-to-the-owasp-top-10)
- [Pick an ASVS level](#pick-an-asvs-level)
- [Keep data out of the code path](#keep-data-out-of-the-code-path)
- [Authenticate users](#authenticate-users)
- [Use OAuth 2.0 and OpenID Connect correctly](#use-oauth-20-and-openid-connect-correctly)
- [Manage sessions and prevent CSRF](#manage-sessions-and-prevent-csrf)
- [Authorise every request](#authorise-every-request)
- [Make outbound requests safely](#make-outbound-requests-safely)
- [Handle secrets](#handle-secrets)
- [Use cryptography conservatively](#use-cryptography-conservatively)
- [Send browser security headers](#send-browser-security-headers)
- [Verify](#verify)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Baseline for every change

1. Treat everything from outside the process as hostile: request bodies, headers, cookies, files, queue messages, webhook payloads, third-party API responses, and model output.
2. Enforce every security decision on the server. Client-side checks are for usability only.
3. Deny by default and grant the least privilege that works, for users, services, tokens and CI jobs alike.
4. Use the framework's built-in protections (escaping, CSRF tokens, parameter binding) and do not turn them off.
5. Never write secrets, tokens, passwords or full personal data to code, logs, errors, URLs or analytics.
6. Prefer a mature library or managed service over your own implementation for authentication, cryptography and sanitisation.

## Map the change to the OWASP Top 10

| OWASP Top 10:2025 category | What to check | Covered in |
|---|---|---|
| A01 Broken Access Control | Object-level and tenant checks on every request | [Authorise every request](#authorise-every-request) |
| A02 Security Misconfiguration | Secure defaults, debug off, headers, least-privilege cloud roles | [Send browser security headers](#send-browser-security-headers), [stack-azure.md](stack-azure.md) |
| A03 Software Supply Chain Failures | New dependencies, lockfiles, CI permissions, provenance | [supply-chain.md](supply-chain.md) |
| A04 Cryptographic Failures | TLS everywhere, vetted algorithms, key handling | [Use cryptography conservatively](#use-cryptography-conservatively) |
| A05 Injection | Parameterised queries, no shell strings, output encoding | [Keep data out of the code path](#keep-data-out-of-the-code-path) |
| A06 Insecure Design | Abuse cases and trust boundaries | [threat-modeling.md](threat-modeling.md) |
| A07 Authentication Failures | Password policy, MFA, session handling, token validation | [Authenticate users](#authenticate-users) |
| A08 Software or Data Integrity Failures | Unsafe deserialisation, unsigned artefacts or updates | [Keep data out of the code path](#keep-data-out-of-the-code-path), [supply-chain.md](supply-chain.md) |
| A09 Security Logging and Alerting Failures | Security events logged and alerted, without secrets | [observability.md](observability.md) |
| A10 Mishandling of Exceptional Conditions | Errors fail closed and do not leak detail | [implementation.md](implementation.md) |

## Pick an ASVS level

Verify against OWASP ASVS 5.0.0 (May 2025). Its developer guide maps Level 1 to first steps, automation or portfolio checks; Level 2 to most applications; Level 3 to high-value, high-assurance or high-safety systems. Target Level 2 for personal/financial data. Cite the version with requirement IDs, which change between releases.

## Keep data out of the code path

Prevent injection by structurally separating code and data, not filtering bad characters.

| Interpreter | Do | Never |
|---|---|---|
| SQL | Parameterised queries or an ORM's bound parameters; allowlist identifiers such as sort columns | Build queries by string concatenation or formatting |
| Shell | Call programs with an argument list and no shell | Pass user input through a shell string |
| HTML | A templating engine with automatic contextual escaping; sanitise rich text with a maintained sanitiser | Insert user input into raw HTML, `innerHTML` or unescaped template blocks |
| File paths | Generate server-side names; resolve the path and confirm it stays inside the allowed directory | Join user input into a path unchecked |
| Deserialisation | Data-only formats such as JSON, parsed into explicit types | Unpickle or binary-deserialise untrusted data, or let the payload choose the type to instantiate |
| Spreadsheet exports | Neutralise cells that begin with formula characters | Write user text into CSV cells unchanged |
| Language model prompts | Treat retrieved and user content as data with clear delimiters, and constrain tools (see [ai-features.md](ai-features.md)) | Assume instructions inside content will be ignored |

Allowlist input shape, length and range at [boundaries](implementation.md). Validation limits interpreter input; it does not replace parameterisation or encoding.

## Authenticate users

1. Delegate sign-in to an established identity provider through OpenID Connect when you can. Building password authentication yourself is a T3 change.
2. If you store passwords, follow NIST SP 800-63B-4: require at least 15 characters for a password used alone and at least 8 when it is one factor of several, allow at least 64 characters, impose no composition rules, never force periodic changes (only on evidence of compromise), and reject passwords found on a blocklist of common or breached values.
3. Hash passwords with Argon2id. OWASP's password storage guidance gives a minimum configuration of 19 MiB of memory, 2 iterations and parallelism 1. Use scrypt where Argon2id is unavailable, bcrypt only in legacy systems (mind its 72-byte input limit), and PBKDF2 when FIPS-140 compliance is required.
4. Offer multi-factor authentication, and require it for administrators and for sensitive actions.
5. Throttle failed attempts per account and per source, and return the same response for an unknown user as for a wrong password.
6. Do not require users to solve puzzles or transcribe codes from memory without an alternative, which WCAG 2.2's accessible authentication criterion addresses (see [accessibility.md](accessibility.md)).

## Use OAuth 2.0 and OpenID Connect correctly

OAuth 2.0's current baseline is RFC 9700 (January 2025).

1. Use the authorisation code flow with PKCE using the `S256` method for every client type. Do not use the implicit grant, and never use the resource owner password credentials grant.
2. Register exact redirect URIs. Authorisation servers must compare them by exact string match.
3. Protect the flow against CSRF with a one-time `state` value bound to the user's browser session, or with PKCE or an OpenID Connect `nonce` when the server supports them.
4. Validate every ID token as OpenID Connect Core requires: issuer matches exactly, your client identifier is in the audience, the signature verifies with the issuer's keys and the expected algorithm, the token has not expired, and the `nonce` matches the one you sent.
5. For any JWT you accept, follow RFC 8725: allowlist the algorithms, reject unsigned tokens, and check issuer, audience and expiry.
6. Request the narrowest scopes, restrict access tokens to their intended audience, and rotate or sender-constrain refresh tokens issued to public clients.
7. For single-page applications, follow RFC 10017 (OAuth 2.0 for Browser-Based Applications), which ranks a backend-for-frontend that keeps tokens out of the browser as the most secure architecture. See [stack-typescript-react.md](stack-typescript-react.md).

## Manage sessions and prevent CSRF

1. Mark session cookies `Secure`, `HttpOnly` and `SameSite` (`Strict` where the flows allow, otherwise `Lax`), and prefer the `__Host-` prefix.
2. Issue a new session identifier at login and at every privilege change, and invalidate the old one.
3. Enforce both an idle timeout and an absolute timeout on the server. Invalidate the session on the server at logout.
4. Protect state-changing requests from cross-site forgery with the framework's token mechanism or a signed double-submit cookie, and check the `Sec-Fetch-Site` or `Origin` header. `SameSite` cookies are defence in depth, not a replacement.
5. Never change state on `GET` requests.

## Authorise every request

1. Check authorisation on the server for every request, for the specific object requested, not only for the route. A missing object-level check (an insecure direct object reference) lets anyone who can change an identifier read other people's data.
2. Scope every query by tenant or owner at the data-access layer, so a forgotten check in one handler cannot leak another tenant's rows.
3. Centralise the policy in one module or service and call it everywhere, rather than scattering role checks.
4. Return 404 instead of 403 where revealing that a resource exists would leak information.
5. Write tests for the denials: another user's object, another tenant's object, a missing role, an expired session.

## Make outbound requests safely

User-influenced server fetches (webhooks, imports, previews, model tools) can attack internal systems.

1. Allowlist destinations where possible, and build the request from fixed scheme, host and port rather than passing a user URL through.
2. Resolve the hostname, reject private, loopback, link-local and cloud metadata addresses, and connect to the address you validated so DNS rebinding cannot swap it.
3. Disable automatic redirects, or re-validate every hop.
4. Restrict egress at the network layer as a second line of defence.

## Handle secrets

1. Keep secrets in a secret manager or the platform's secret store, injected at runtime. Use workload identities instead of long-lived keys where the platform supports them.
2. Give each workload its own credentials with the least privilege it needs, and rotate them on a schedule, automatically where possible.
3. Run secret scanning in pre-commit hooks and in CI. The bundled [change scanner](../scripts/change_scan.py) flags likely secrets in a diff without printing them.
4. If a secret leaks, revoke and replace it first. Removing it from history comes second, because the value is already exposed.

## Use cryptography conservatively

1. Use TLS for all network traffic, internal included. NIST SP 800-52 Rev. 2 requires TLS 1.2 as the minimum and support for TLS 1.3; prefer 1.3.
2. Never implement cryptographic primitives or protocols yourself. Use a maintained high-level library with safe defaults, such as authenticated encryption.
3. Generate tokens, keys and identifiers that must be unguessable with the platform's cryptographically secure random generator.
4. Compare secrets and signatures in constant time.
5. Keep keys in a key management service, separate from the data they protect, and plan rotation before you need it.

## Send browser security headers

| Header | Recommended starting value |
|---|---|
| `Content-Security-Policy` | A strict policy without `unsafe-inline`; include `frame-ancestors 'none'` or a named list |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` (add `preload` only after checking every subdomain serves HTTPS) |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Disable unused features, for example `geolocation=(), camera=(), microphone=()` |
| `Cross-Origin-Opener-Policy` | `same-origin` |

Omit `X-XSS-Protection` or set it to `0`; never use `Expect-CT` or `Public-Key-Pins`.

## Verify

1. Run the repository's static analysis, dependency audit and secret scan, and read new findings in the files you touched.
2. Add tests for each threat-model mitigation and each authorisation rule, including negative cases.
3. For T3 changes, ask for a security-focused human review, and record which ASVS requirements were checked.

- [ ] No user-controlled data reaches an interpreter except through parameters or encoding.
- [ ] Every new endpoint has an authorisation test for a denied caller.
- [ ] No secret appears in the diff, logs or error messages.
- [ ] Tokens are validated for issuer, audience, expiry and signature.

## Failure modes

- Checking login without record ownership.
- JWT libraries trusting token-selected algorithms.
- Treating deletion of committed "temporary" keys as revocation.
- Image previews fetch `http://169.254.169.254/` and leak cloud credentials.
- Untested copied headers break login; teams disable all protection to compensate.

## Sources

- OWASP, [Top 10:2025](https://owasp.org/Top10/2025/), lists the categories mapped above.
- OWASP, [ASVS](https://asvs.owasp.org/), and the [OWASP Developer Guide on ASVS](https://devguide.owasp.org/en/03-requirements/05-asvs/) describe the standard and its levels.
- NIST, [SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html), sets the password rules summarised above.
- OWASP Cheat Sheet Series: [Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [SSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html), [Deserialization](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html), [Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) and [HTTP Headers](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html). They are CC BY-SA, so this file summarises them in its own words.
- IETF, [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html) (OAuth 2.0 security), [RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html) (JWT practices) and [RFC 10017](https://www.rfc-editor.org/rfc/rfc10017.html) (browser-based applications).
- OpenID Foundation, [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html), section 3.1.3.7, defines ID token validation.
- NIST, [SP 800-52 Rev. 2](https://csrc.nist.gov/pubs/sp/800/52/r2/final), sets the TLS version requirements.
