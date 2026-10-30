# Data and privacy

Use for schemas, migrations, backfills, data movement/transformation/deletion, new datastores and personal data.

## Contents

- [Treat data changes as high risk](#treat-data-changes-as-high-risk)
- [Change schemas in expand and contract steps](#change-schemas-in-expand-and-contract-steps)
- [Run migrations without downtime](#run-migrations-without-downtime)
- [Let the database protect integrity](#let-the-database-protect-integrity)
- [Back up, and prove you can restore](#back-up-and-prove-you-can-restore)
- [Handle personal data by design](#handle-personal-data-by-design)
- [Delete data completely](#delete-data-completely)
- [Keep production data out of other environments](#keep-production-data-out-of-other-environments)
- [Escalate suspected breaches at once](#escalate-suspected-breaches-at-once)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Treat data changes as high risk

Data loss or corruption may outlast code rollback. Migrations/backfills are at least T2; T3 if dropping/rewriting data, touching large/hot tables or changing personal-data handling. Destructive operations (drop, truncate, mass update/delete) require explicit user approval, a verified backup and a written rollback plan.

## Change schemas in expand and contract steps

Deploys are not atomic: every schema state must support old and new code during rollout and rollback.

Example: rename `fullname` to `display_name`:

1. Expand: add `display_name` as a nullable column. Old code ignores it.
2. Deploy code that writes both columns and reads the old one.
3. Backfill `display_name` from `fullname` in small batches, with progress logging, and make the backfill safe to rerun.
4. Deploy code that reads `display_name`, falling back to `fullname` if empty, and still writes both.
5. Once all readers use the new column and a rollback window has passed, stop writing `fullname`.
6. Contract: drop `fullname` in a later release, after confirming nothing reads it.

Never rename/retype live columns in place or combine expand and contract in one deploy.

## Run migrations without downtime

Examples use PostgreSQL; check other databases' documentation for equivalent operations and lock behaviour.

1. Know the locks. Most `ALTER TABLE` forms take an `ACCESS EXCLUSIVE` lock that blocks reads and writes. Set a short `lock_timeout` so a migration waiting behind a long transaction fails fast instead of queueing every query behind it.
2. Create indexes on live tables with `CREATE INDEX CONCURRENTLY`. It does not block writes, cannot run inside a transaction block, and leaves an `INVALID` index behind if it fails, which you must drop and recreate.
3. Add a column with a constant (non-volatile) default freely: since PostgreSQL 11 this stores the default in metadata without rewriting the table. A volatile default such as `clock_timestamp()` rewrites the whole table.
4. Add a constraint to a large table in two steps: add it as `NOT VALID` (enforced for new rows only), then run `VALIDATE CONSTRAINT`, which takes a weaker lock and lets normal traffic continue.
5. Backfill in batches of a bounded size with a pause between them, outside the schema migration transaction, and watch replication lag and lock waits while it runs.
6. Run migrations as a separate, observable step of the release, not silently at application start-up on every instance.
7. Review every generated migration line by line. Migration tools miss renames (they emit a drop and an add) and some constraint and type changes.
8. Rehearse large migrations against a production-sized copy and time them.

Bad:

```sql
ALTER TABLE orders RENAME COLUMN fullname TO display_name;
CREATE INDEX orders_customer_idx ON orders (customer_id);
```

Good:

```sql
SET lock_timeout = '3s';
ALTER TABLE orders ADD COLUMN display_name text;
-- run outside a transaction block:
CREATE INDEX CONCURRENTLY orders_customer_idx ON orders (customer_id);
```

## Let the database protect integrity

1. Declare constraints in the schema: `NOT NULL`, unique keys, foreign keys and check constraints. Application code has bugs and races; constraints hold for every writer.
2. Wrap multi-step changes that must succeed or fail together in a transaction, and keep transactions short.
3. Choose the isolation level deliberately for read-then-write logic, or use conditional updates and optimistic concurrency with a version column.
4. Make data pipelines and backfills idempotent so a rerun after a partial failure produces the same result.

## Back up, and prove you can restore

Google SRE's point: people need restores, not merely backups.

1. Define the recovery point objective (how much data you can lose) and the recovery time objective (how long recovery may take) for each datastore, and choose backup frequency and method to meet them.
2. Test restores automatically and regularly, and alert when a restore test stops succeeding. An untested backup is a hope.
3. Layer your defences: soft deletion for user mistakes, backups for larger losses, and data validation to catch silent corruption.
4. Remember that replication is not a backup. It copies deletions and corruption to every replica within seconds.
5. Take and verify a backup or snapshot before any T3 data migration.

## Handle personal data by design

GDPR Article 5 principles: lawfulness, fairness/transparency, purpose limitation, minimisation, accuracy, storage limitation, integrity/confidentiality and accountability. Article 25 requires data protection by design/default. Use these engineering defaults even outside GDPR's scope.

1. Classify each new field: personal, special category (health, biometrics and similar), financial, credentials, or non-personal. Record the classification next to the schema.
2. Collect only what the feature needs, for a stated purpose, and do not reuse it for an unrelated purpose without review.
3. Define a retention period for each kind of personal data and implement deletion or anonymisation when it expires.
4. Restrict access to the minimum, log access to sensitive data, and encrypt it in transit and at rest. Pseudonymise where analysis does not need identities.
5. Know where data is stored and processed, including in third-party services and model providers, and check that location and processor terms are approved.
6. Flag to the user any new processing that is likely to be high risk, such as large-scale special category data, profiling or systematic monitoring. Article 35 may require a data protection impact assessment before it starts, and that is a decision for humans.

## Delete data completely

1. Trace every copy before you build deletion: primary store, replicas, caches, search indexes, analytics and data warehouses, files and object storage, logs, third-party processors and backups.
2. Delete or anonymise in every live copy, and let backups expire on a documented schedule rather than editing them.
3. Write a test that creates a record, deletes it, and confirms it no longer appears in each place the application can query.

## Keep production data out of other environments

1. Use synthetic data or factories for development and testing.
2. Use masked or anonymised copies of production data only with approval and with the same access controls as production.
3. Never paste personal data into prompts, tickets, chat, commit messages or test fixtures.

## Escalate suspected breaches at once

GDPR Article 33 requires controllers to notify the supervisory authority without undue delay, where feasible within 72 hours of discovering a personal-data breach. On exposure (public buckets, leaked logs, missing access checks), stop, preserve evidence and tell the user immediately. Do not quietly fix first or independently dismiss reporting obligations.

- [ ] The migration is backward compatible with the currently deployed code and with a rollback.
- [ ] Lock behaviour of each statement is known, and large tables use concurrent or two-step operations.
- [ ] A verified backup exists before destructive steps, and a restore has been tested recently.
- [ ] New personal data has a classification, a purpose and a retention period.

## Failure modes

- One-deploy column renames break old instances throughout rollout.
- Busy-table index builds block writes for twenty minutes at peak hours.
- A migration waiting behind a long report queues all other queries.
- Years of nightly backups fail their first restore during an incident.
- Database deletion leaves personal data in search indexes and analytics exports.
- Copying production customer data to a developer laptop for debugging.

## Sources

- Danilo Sato, [Parallel Change](https://martinfowler.com/bliki/ParallelChange.html), describes the expand, migrate and contract phases.
- PostgreSQL documentation, [CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html) and [ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html), define the lock levels, concurrent index builds, `NOT VALID` constraints and fast column defaults described above.
- Google's SRE book, [Data Integrity: What You Read Is What You Wrote](https://sre.google/sre-book/data-integrity/), covers restores, restore testing and defence in depth.
- [Regulation (EU) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) is the official text; readable article pages for [Article 5](https://gdpr-info.eu/art-5-gdpr/), [Article 25](https://gdpr-info.eu/art-25-gdpr/) and [Article 33](https://gdpr-info.eu/art-33-gdpr/) are published separately. This file is engineering guidance, not legal advice.
