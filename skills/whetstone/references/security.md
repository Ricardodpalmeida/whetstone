# Security

Use for a changed trust boundary, authentication, permissions, untrusted input or secrets. Review the specific path being changed; do not audit an unrelated application by default.

## Identify the failure to prevent

List the protected asset, who can influence the input, where authority changes and how the new path could be abused. Connect each material threat to a control and a check. A short PR note is enough when it captures the decision; reuse an existing threat model when one exists.

## Controls that must survive

| Boundary | Check |
|---|---|
| Object or tenant access | Enforce authorization server-side for the requested object. Test another owner's identifier, not just an unauthenticated request. Deny access if the policy check fails. |
| SQL or shell | Bind values or pass an argument list. Validate identifiers separately; escaping a shell string is not the default design. |
| HTML, files or exports | Use contextual encoding or a maintained sanitizer. Resolve paths within the authorized root, accounting for symlinks. Constrain upload size/type and prevent spreadsheet formula execution from untrusted cells. |
| Server-side URL fetch | Restrict destinations, validate resolved addresses and redirects, and prevent DNS rebinding. Do not let arbitrary input reach internal or metadata endpoints. |
| Secrets | Use the existing secret store and least-privilege identity. Redact diagnostics. Revoke an exposed credential; removing its text does not revoke it. |

## Sign-in and sessions

Use a maintained identity library. For OpenID Connect, verify the installed library's authorization-code/PKCE setup, exact redirect URI matching, request correlation and ID-token validation: signature, allowed algorithm, issuer, audience, expiry and nonce when used. Decide how accounts link; an email claim alone is not a safe account-linking policy.

For sessions, preserve secure cookie settings, CSRF protection, session renewal at login/privilege changes and server-side expiry/revocation. A signed cookie can still expose its contents. Keep password policy and hashing parameters aligned with the project's current security requirements and the linked NIST/OWASP guidance rather than copying old defaults.

Use established cryptography and framework protections. Do not add blanket security headers or replace an authentication system without checking affected integrations. Preserve existing access until the replacement has been verified within the authorized change.

## Verify the boundary

Exercise denial, malformed input and dependency failure, as well as the successful path. For outbound calls, test disallowed destinations and redirect handling. For state-changing operations, test the caller's authority and replay/concurrency behavior. Record an unresolved material exposure before release.

## Sources

- [OWASP authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [NIST authentication guidance](https://pages.nist.gov/800-63-4/sp800-63b.html)
- [OAuth security, RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)
- [OpenID Connect token validation](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation)
