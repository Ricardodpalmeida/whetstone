# Testing

Use for behaviour changes, bug fixes and choosing test scope.

## Contents

- [Decide what to test](#decide-what-to-test)
- [Choose the level](#choose-the-level)
- [Write the test first when it helps](#write-the-test-first-when-it-helps)
- [Write tests that earn trust](#write-tests-that-earn-trust)
- [Use test doubles sparingly](#use-test-doubles-sparingly)
- [Cover the edges](#cover-the-edges)
- [Generate inputs with property-based tests](#generate-inputs-with-property-based-tests)
- [Check contracts between services](#check-contracts-between-services)
- [Measure test quality](#measure-test-quality)
- [Keep the suite trustworthy](#keep-the-suite-trustworthy)
- [Never weaken a test to pass](#never-weaken-a-test-to-pass)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Decide what to test

Test what must not break. Google's Beyoncé Rule: "If you liked it, then you shoulda put a test on it."

| Tier | Minimum testing |
|---|---|
| T0 | Run any existing check that covers the file (link checker, docs build, formatter). |
| T1 | Existing tests pass. Add or update a unit test when behaviour changes. |
| T2 | Unit and integration tests for the new behaviour, including negative paths. A regression test for every bug fix. |
| T3 | T2 plus end-to-end tests of critical journeys, contract tests for changed interfaces, tests for each threat-model mitigation, load tests where an SLO is at stake, and a rehearsed migration and rollback. |

Prioritise likely/costly defects: complex logic, money, permissions, transformations, concurrency and frequently changed code.

## Choose the level

The test pyramid uses multiple granularities with fewer higher-level tests; the frontend testing trophy favours integration. Both optimise confidence per unit of time.

| Level | Use it for | Keep it |
|---|---|---|
| Static checks (types, linters) | Whole classes of mistakes at no runtime cost | Always on, failing the build |
| Unit | Logic in one function, class or module | Fast, in-process, no network or disk |
| Integration | Your code with a real database, queue or framework | Real dependencies in containers, isolated data per test |
| Contract | Agreement between a consumer and a provider | Run in both pipelines |
| End-to-end | A few critical user journeys | Few, stable, owned |

Prefer real containerised dependencies over mocks when testing integration itself: SQL, serialisation or migrations.

## Write the test first when it helps

Test-first fits reproducible bugs and logic with clear inputs/outputs. Kent Beck's "Canon TDD" loop:

1. Write a list of the behaviours to cover, including existing behaviour that must not break.
2. Turn one item into a real test, with setup, action and assertions.
3. Change the code until that test and all previous ones pass.
4. Optionally refactor, with the tests green.
5. Repeat until the list is empty.

## Write tests that earn trust

1. Test behaviour through public interfaces, not private implementation details, so refactoring does not break tests.
2. Give each test one reason to fail and a name that states the behaviour: `rejects_expired_token`, not `test_token_3`.
3. Structure each test as arrange, act, assert. Keep loops and conditionals out of test code.
4. Make tests deterministic: control time, randomness, ordering and concurrency, and never depend on another test's leftovers.
5. Compute expected values independently. Copying the code's own output into the assertion checks nothing.
6. Build test data with small factories that set only the fields that matter to the test. Never copy production personal data into fixtures.
7. Test user interfaces the way people use them. Testing Library's guiding principle is that "the more your tests resemble the way your software is used, the more confidence they can give you", so query elements by role and accessible name (see [accessibility.md](accessibility.md)).

## Use test doubles sparingly

Fowler distinguishes dummies, fakes, stubs, spies and mocks. Use the weakest sufficient double.

1. Prefer real objects, then fakes (working lightweight implementations such as an in-memory repository), then stubs. Use mocks that verify calls only when the call itself is the behaviour, for example "sends exactly one email".
2. Double only at boundaries you control. Wrap third-party clients in a thin adapter of your own and double the adapter.
3. Never double the unit under test, and never assert on a mock's configuration in place of real output.

## Cover the edges

Inputs: empty, single, many, maximum size, both sides of boundaries, null/missing, wrong type, duplicates, non-ASCII and malicious content.

Dependencies: success, slow response, timeout, errors, malformed responses and partial failure.

Operations: unauthenticated, unauthorised and cross-tenant callers; concurrent modification; retries; time-zone and daylight-saving boundaries.

## Generate inputs with property-based tests

Property-based tests generate inputs and shrink failures. Use for parsers, serialisers, encoders, sorting, pricing and inverse operations.

Properties: round-tripping (`decode(encode(x)) == x`), invariants (non-negative totals), idempotence (normalise twice = once), and agreement with a simpler reference. Libraries include Python's Hypothesis, JS/TS fast-check and .NET FsCheck.

## Check contracts between services

1. When you own both sides or know every consumer, use consumer-driven contract tests (for example Pact), so a provider learns before deploying that it would break a consumer.
2. For public APIs with unknown consumers, validate requests and responses against the published schema (OpenAPI or AsyncAPI) in the provider's test suite, and check every change for backward compatibility (see [api-design.md](api-design.md)).

## Measure test quality

Coverage measures execution, not assertions. Google's testing blog suggests 60 percent acceptable, 75 commendable and 90 exemplary overall; 90 percent of changed lines as a lower threshold. Avoid checkbox targets.

1. Look at coverage of the lines you changed and read what is uncovered. Each uncovered branch is either a missing test or dead code.
2. Run mutation testing (for example mutmut for Python or Stryker for JavaScript, TypeScript and C#) on critical modules. A surviving mutant points to an assertion that is missing.
3. Never add tests without assertions to raise a number.

## Keep the suite trustworthy

Flaky tests vary on unchanged code. Google reported almost 16 percent showing flakiness and about 84 percent of post-submit pass-to-fail transitions involving flaky tests. This erodes trust in red builds.

1. Treat a flaky test as a bug. Reproduce it in a loop and find the cause with [debugging.md](debugging.md).
2. If a test must be quarantined to unblock others, agree it with the user, file an issue with an owner and a date, and keep running the test outside the blocking path.
3. Do not add automatic retries that hide intermittent failures. They can mask a real race condition.
4. Keep the fast suite fast. When the unit suite becomes slow, find and fix the slow tests instead of running them less often.

## Never weaken a test to pass

Require explicit user agreement and a PR rationale before deleting/loosening assertions, skipping/disabling tests, widening tolerances/timeouts without measured cause, catching test exceptions to stay green, editing snapshots without diff review, or matching expected values to new output without explaining why the old expectation was wrong. Intentional behaviour changes require corresponding tests and an explanation in the same change.

- [ ] Every new behaviour has a test that fails without the change.
- [ ] Every bug fix has a regression test that failed before the fix.
- [ ] No test was skipped, deleted or loosened without an explicit reason in the PR.
- [ ] The suite passes twice in a row locally or in CI.

## Failure modes

- Mocking every collaborator hides real integration failures.
- Implementation-coupled assertions break dozens of tests per refactor and discourage refactoring.
- High coverage with weak assertions lets most mutations survive.
- Retrying flaky tests to green makes builds meaningless.
- Changing assertions to match incorrect new output.

## Sources

- *Software Engineering at Google*, [Testing Overview](https://abseil.io/resources/swe-book/html/ch11.html), defines test sizes and the Beyoncé Rule quoted above.
- Ham Vocke, [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html), states the pyramid's two rules.
- Kent C. Dodds, [The Testing Trophy and Testing Classifications](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications), argues for weighting integration tests.
- Kent Beck, [Canon TDD](https://tidyfirst.substack.com/p/canon-tdd), describes the test-list loop and its common mistakes.
- Martin Fowler, [Test Double](https://martinfowler.com/bliki/TestDouble.html), defines the kinds of test doubles.
- Google Testing Blog, [Code Coverage Best Practices](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html) and [Flaky Tests at Google and How We Mitigate Them](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html), supply the coverage guidance and flakiness figures.
- [Testing Library's guiding principles](https://testing-library.com/docs/guiding-principles/) is the source of the quotation on tests that resemble real use.
- [Pact](https://docs.pact.io/) documents consumer-driven contract testing and where it fits.
- Property-based and mutation testing tools: [Hypothesis](https://hypothesis.readthedocs.io/en/latest/), [fast-check](https://fast-check.dev/), [FsCheck](https://fscheck.github.io/FsCheck/), [mutmut](https://mutmut.readthedocs.io/) and [Stryker](https://stryker-mutator.io/).
