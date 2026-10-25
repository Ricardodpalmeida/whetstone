# Supply chain

Read this when you add, upgrade or remove a dependency, change a build or CI/CD pipeline, or publish an artefact. OWASP ranks Software Supply Chain Failures third in its Top 10:2025.

## Contents

- [Decide whether you need the dependency](#decide-whether-you-need-the-dependency)
- [Confirm the package is real](#confirm-the-package-is-real)
- [Evaluate it before adopting it](#evaluate-it-before-adopting-it)
- [Pin and lock](#pin-and-lock)
- [Update deliberately](#update-deliberately)
- [Scan and triage vulnerabilities](#scan-and-triage-vulnerabilities)
- [Harden the pipeline](#harden-the-pipeline)
- [Know what you ship](#know-what-you-ship)
- [Respect licences](#respect-licences)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Decide whether you need the dependency

Every dependency is code you run without having written or reviewed it, plus everything it depends on.

Apply it:

1. Check whether the standard library, the framework or an existing dependency already does the job.
2. Write a small function yourself when the need is a few lines of well-understood code. Do not add a package for padding a string or checking a type.
3. Treat a new runtime dependency as at least a T2 change, and a new framework, datastore client or native-code package as a T3 trigger. State in the PR why the dependency is needed and what alternatives you considered.

## Confirm the package is real

Language models invent package names. A USENIX Security 2025 study of 16 code-generating models found hallucinated package names in at least 5.2 percent of samples from commercial models and 21.7 percent from open-source models. Attackers register such names, and look-alike names of popular packages, to deliver malware.

Apply it:

1. Before installing anything, confirm the exact name in the official registry and on the project's own website or repository. Check that the repository links back to the package.
2. Compare the name character by character with the package you meant. Watch for transposed letters, swapped hyphens and underscores, and scope changes.
3. Be suspicious of packages that are very new, have few downloads, have no repository link, or run install scripts.
4. Never pipe a downloaded script straight into a shell. Download it, read it, then run it.

## Evaluate it before adopting it

The OpenSSF "Concise Guide for Evaluating Open Source Software" gives a checklist. In short, check:

| Question | Evidence to look for |
|---|---|
| Is it maintained? | Meaningful commits or releases in the last 12 months, more than one maintainer |
| Does it take security seriously? | A security policy, a vulnerability reporting route, timely fixes, automated tests |
| Is it widely used for this purpose? | Real adoption, issues answered, not just popularity |
| Does it have known unfixed vulnerabilities? | Advisories for the version you would use, and how long they stayed open |
| Is the licence clear and compatible? | A standard OSI-approved licence that fits your distribution model |
| How does it score? | The OpenSSF Scorecard result, which checks items such as Maintained, Code-Review, Pinned-Dependencies, Token-Permissions and Vulnerabilities |

Check transitive dependencies too: a small package that pulls in a hundred others is not small.

## Pin and lock

Apply it:

1. Commit the lockfile for every application, and install from it in CI and production with the package manager's frozen or locked mode, so builds are reproducible.
2. Prefer lockfiles that record integrity hashes, and fail the install when a hash does not match.
3. Pin container base images by digest, and CI actions or reusable workflows by full commit SHA.
4. For libraries you publish, declare compatible version ranges in the manifest, but still lock the versions used to build and test them.

## Update deliberately

Staying current is a security control: old versions accumulate known vulnerabilities. Updating the moment a release appears is also a risk, because malicious releases are usually caught within days.

Apply it:

1. Use an update bot (for example Dependabot or Renovate) so updates arrive as small, reviewable PRs with release notes.
2. Configure a waiting period before routine version updates. Dependabot's `cooldown` option defaults to 3 days for version updates and does not delay security updates; Renovate offers `minimumReleaseAge` for the same purpose.
3. Keep security updates fast. Apply them promptly after reviewing the advisory and running the tests.
4. Read the changelog for major versions, and keep one dependency change per PR unless the updates are grouped on purpose.
5. Never upgrade dependencies as a side effect of an unrelated change.

## Scan and triage vulnerabilities

Apply it:

1. Run the ecosystem's audit in CI against the lockfile: for example `npm audit`, `pip-audit`, the NuGet audit that runs during `dotnet restore`, or OSV-Scanner across ecosystems using the OSV database.
2. Triage each finding: is the vulnerable code reachable from your code, is a fixed version available, and what is the exposure?
3. Upgrade when a fix exists. Otherwise mitigate (configuration, input restrictions, removing the feature) or accept the risk with an owner and an expiry date, and record the decision.
4. Fail the build on new high and critical findings in production dependencies. Avoid failing on every low-severity advisory, or people learn to ignore the check.

## Harden the pipeline

The pipeline holds the keys to production, so it is an attack target.

Apply it:

1. Set the default `GITHUB_TOKEN` (or the equivalent CI token) to read-only, and grant extra permissions per job only where needed.
2. Pin third-party actions to a full-length commit SHA from the action's own repository, not a mutable tag.
3. Never expose secrets to workflows triggered by untrusted pull requests, and never interpolate untrusted event fields (titles, branch names, comments) directly into shell scripts. OpenSSF Scorecard's Dangerous-Workflow check looks for these patterns.
4. Authenticate deployments to cloud providers with short-lived federated credentials (OIDC) instead of long-lived keys stored as secrets.
5. Protect the default branch: require reviews and passing checks, and block force pushes.
6. Treat pipeline changes as T2 or above, and review them as carefully as application code.

## Know what you ship

Apply it:

1. Generate a software bill of materials (SBOM) for each release artefact, in CycloneDX (currently 1.7) or SPDX (currently 3.0) format, from the build itself rather than from a manifest guess.
2. Produce build provenance. SLSA v1.2's Build track defines L1 (provenance exists), L2 (a hosted build platform generates and signs the provenance) and L3 (a hardened platform isolates builds and keeps signing secrets away from build steps). Hosted CI with signed provenance reaches L2.
3. Sign release artefacts and container images (for example with Sigstore), and verify the signature and provenance before deploying.
4. Follow NIST's Secure Software Development Framework (SP 800-218) when a customer or regulator asks for an attested secure development process.

## Respect licences

Apply it:

1. Check the licence of every new dependency against how you distribute the software. Copyleft licences can impose obligations on distributed or network-served code.
2. Never paste code from a source whose licence you have not checked, and never paste code from incompatible licences into the codebase.
3. Record attributions that a licence requires, in the project's notices file.

Check:

- [ ] Every new dependency is justified in the PR, verified as the genuine package, and evaluated.
- [ ] The lockfile is committed and CI installs from it.
- [ ] CI actions are pinned by commit SHA and tokens are least-privilege.
- [ ] No new high or critical vulnerability is introduced without a recorded decision.

## Failure modes

- An agent adds a dependency whose name it invented, and an attacker has already registered that name.
- A floating version range pulls a compromised release into production on the next build.
- A workflow triggered by an external pull request runs untrusted code with access to deployment secrets.
- Vulnerability alerts pile up unread because the scanner fails builds on every low-severity advisory.
- A copyleft dependency is shipped inside a proprietary product without anyone checking.

## Sources

- OWASP, [Top 10:2025](https://owasp.org/Top10/2025/), lists A03:2025 Software Supply Chain Failures.
- Spracklen and others, [We Have a Package for You!](https://arxiv.org/abs/2406.10279), measured package hallucination by code-generating models (USENIX Security 2025).
- OpenSSF, [Concise Guide for Evaluating Open Source Software](https://best.openssf.org/Concise-Guide-for-Evaluating-Open-Source-Software), and the [Scorecard checks](https://github.com/ossf/scorecard/blob/main/docs/checks.md) underpin the evaluation table.
- GitHub, [Dependabot options reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference), documents `cooldown`; Renovate documents [`minimumReleaseAge`](https://docs.renovatebot.com/configuration-options/#minimumreleaseage).
- GitHub, [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use), recommends SHA pinning and least-privilege tokens.
- [OSV](https://osv.dev/) aggregates vulnerability advisories; Microsoft documents [NuGet package auditing](https://learn.microsoft.com/en-us/nuget/concepts/auditing-packages).
- [SLSA v1.2 Build track basics](https://slsa.dev/spec/v1.2/build-track-basics), [CycloneDX](https://cyclonedx.org/specification/overview/), [SPDX](https://spdx.dev/use/specifications/) and [Sigstore](https://www.sigstore.dev/) define provenance, SBOM formats and signing.
- NIST, [SP 800-218 (SSDF)](https://csrc.nist.gov/pubs/sp/800/218/final), describes secure development practices.
