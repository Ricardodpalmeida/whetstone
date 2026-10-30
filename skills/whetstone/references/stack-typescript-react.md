# Stack notes: TypeScript and React

Add these stack-specific notes to core references for TypeScript/JavaScript, React and Node.js.

## Contents

- [Handle fetch failures and timeouts](#handle-fetch-failures-and-timeouts)
- [Keep secrets out of the bundle](#keep-secrets-out-of-the-bundle)
- [Keep tokens out of the browser](#keep-tokens-out-of-the-browser)
- [Prevent cross-site scripting in React](#prevent-cross-site-scripting-in-react)
- [Use the type system honestly](#use-the-type-system-honestly)
- [Test components and accessibility](#test-components-and-accessibility)
- [Other JavaScript traps](#other-javascript-traps)
- [Sources](#sources)

## Handle fetch failures and timeouts

`fetch` resolves HTTP errors such as 404/504, rejecting only request failures; it has no default timeout.

1. Check `response.ok` (or the status) on every response, and turn failures into typed errors.
2. Pass `signal: AbortSignal.timeout(ms)` to every request, and combine it with the caller's abort signal where one exists.
3. Validate response bodies at runtime against a schema before use. A TypeScript type annotation on `response.json()` checks nothing at runtime.

Bad:

```ts
const user = (await (await fetch(`/api/users/${id}`)).json()) as User;
```

Good:

```ts
const res = await fetch(`/api/users/${encodeURIComponent(id)}`, {
  signal: AbortSignal.timeout(5000),
});
if (!res.ok) throw new ApiError(res.status, await res.text());
const user = UserSchema.parse(await res.json());
```

## Keep secrets out of the bundle

Browser bundles are public. Vite exposes `VITE_` variables at build time; never put API keys or other sensitive data in them.

1. Put API keys, client secrets and service credentials only on a server: your back end, a backend-for-frontend, or a serverless function.
2. Treat any value read in browser code as visible to every user, including values in source maps and local storage.
3. Search the built bundle for known secret patterns before release, or rely on the CI secret scanner (see [supply-chain.md](supply-chain.md)).

## Keep tokens out of the browser

RFC 10017, OAuth 2.0 for Browser-Based Applications (August 2026), ranks three architectures by security, BFF first. This confidential backend client keeps tokens in a server-side session behind a secure cookie and proxies API calls, leaving none in the browser to steal. It strongly recommends BFF for business, sensitive and personal-data applications.

1. For new single-page applications that call protected APIs, use a BFF with `HttpOnly`, `Secure`, `SameSite` session cookies and CSRF protection (see [security.md](security.md)).
2. If a BFF is truly impossible, use the authorisation code flow with PKCE, short-lived access tokens, and refresh token rotation; never the implicit flow.
3. Do not store access or refresh tokens in `localStorage` or `sessionStorage`, where any injected script can read them.
4. Restrict the BFF's proxy to an allowlist of upstream destinations.

## Prevent cross-site scripting in React

React's JSX escaping prevents most XSS; bypasses remain dangerous.

1. Avoid `dangerouslySetInnerHTML`. When rich HTML is unavoidable, sanitise it with a maintained HTML sanitiser configured with an allowlist, immediately before rendering.
2. Validate URLs from users or data before putting them in `href` or `src`, and allow only `https:` (and `mailto:` where needed), because `javascript:` URLs execute script.
3. Never build HTML strings for `innerHTML`, `document.write` or `eval`-like APIs from data.
4. Send a Content Security Policy without `unsafe-inline` as a second line of defence (see [security.md](security.md)).

## Use the type system honestly

1. Enable `strict` mode in `tsconfig.json` and keep it on.
2. Avoid `any`, non-null assertions (`!`) and broad type assertions (`as`) at boundaries. Use `unknown` and parse with a runtime schema instead.
3. Model states as discriminated unions (`{ status: "loading" } | { status: "error"; error: ApiError } | { status: "ready"; data: User }`) so impossible states cannot be represented.
4. Do not add `@ts-ignore` or `@ts-expect-error` without a comment explaining why and a tracked issue.

## Test components and accessibility

1. Test components through what users see and do, following Testing Library's principle that tests resembling real use give more confidence: query by role and accessible name, not by CSS class or test identifiers where a role exists.
2. Run axe-core in end-to-end tests, for example with `@axe-core/playwright`, filtered to WCAG A and AA tags, and fail on new violations (see [accessibility.md](accessibility.md)).
3. Use fast-check for property-based tests of parsers and pure logic, and Stryker for mutation testing of critical modules (see [testing.md](testing.md)).
4. Mock the network at the HTTP boundary rather than mocking your own modules, so tests exercise real request and response handling.

## Other JavaScript traps

- Handle every promise: `await` it or attach a rejection handler. Unhandled rejections can crash a Node.js process or vanish silently in the browser.
- Use `===`, and parse numbers explicitly; implicit coercion turns `"10" + 1` into `"101"`.
- Represent money in integer minor units; JavaScript numbers are binary floating point.
- Be careful with dates: `new Date("2026-03-01")` is parsed as midnight UTC, but `new Date("2026-03-01T00:00")` is parsed as local time. Use a well-tested date library or the standard `Temporal` API where available.
- Clean up effects in React: return a cleanup function that aborts in-flight requests and removes listeners, so unmounted components do not update state.
- Commit the lockfile and install with `npm ci` (or the equivalent for your package manager) in CI.

## Sources

- MDN, [Window: fetch() method](https://developer.mozilla.org/en-US/docs/Web/API/Window/fetch), [AbortSignal.timeout()](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static) and [Date.parse()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/parse), which shows date-only strings read as UTC and date-time strings without an offset read as local time.
- Vite, [Env Variables and Modes](https://vite.dev/guide/env-and-mode), on `VITE_` variables and secrets.
- IETF, [RFC 10017 OAuth 2.0 for Browser-Based Applications](https://www.rfc-editor.org/rfc/rfc10017.html), describes the backend-for-frontend, token-mediating backend and browser-based client architectures.
- [Testing Library guiding principles](https://testing-library.com/docs/guiding-principles/); Playwright, [Accessibility testing](https://playwright.dev/docs/accessibility-testing).
- [fast-check](https://fast-check.dev/) and [Stryker](https://stryker-mutator.io/).
