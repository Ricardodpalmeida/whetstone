# Stack notes: data platforms

Add these data-specific notes to core references for pipelines, warehouse/lakehouse models, dbt, Spark/Delta Lake, notebooks and scheduled extracts/loads.

## Contents

- [Make pipelines idempotent](#make-pipelines-idempotent)
- [Test the data, not only the code](#test-the-data-not-only-the-code)
- [Change schemas without breaking consumers](#change-schemas-without-breaking-consumers)
- [Backfill safely](#backfill-safely)
- [Handle time explicitly](#handle-time-explicitly)
- [Treat notebooks and schedules as production code](#treat-notebooks-and-schedules-as-production-code)
- [Observe freshness, volume and cost](#observe-freshness-volume-and-cost)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Make pipelines idempotent

Jobs fail mid-run and streams replay after restart. Twice processing the same input must equal processing it once.

1. Write outputs by overwriting a well-defined partition, or by upserting with `MERGE` on a business key, never by blind appends.
2. In Spark Structured Streaming, make any `MERGE` inside `foreachBatch` idempotent, because a restart can reapply the same micro-batch; Delta Lake's documentation calls this out.
3. Derive outputs only from inputs and parameters (such as the processing date), not from the wall clock at run time.
4. Record a run identifier and the input watermark with each load, so you can see what was processed and rerun a specific range.
5. Send records that fail validation to a quarantine table with the reason, rather than dropping them silently or failing the whole run for one bad row.

## Test the data, not only the code

1. Declare tests on every model's key columns. dbt ships four generic tests: `unique`, `not_null`, `accepted_values` and `relationships`; each compiles to a query that returns failing rows, so zero rows means a pass.
2. Add source checks for schema, freshness and volume, so an upstream change or an empty extract stops the pipeline instead of publishing wrong numbers.
3. Unit test transformation logic with small, hand-built input tables and expected outputs, including nulls, duplicates, late records and boundary dates.
4. Set test severity deliberately: block publication on errors that would mislead consumers, and warn on the rest.
5. Reconcile totals against the source system for financial or regulatory figures.

## Change schemas without breaking consumers

Externally queried tables/models are [API-like contracts](api-design.md).

1. Add columns rather than renaming or retyping them. For unavoidable changes, publish the new column or model alongside the old one, migrate consumers, then remove the old one (see [data-and-privacy.md](data-and-privacy.md)).
2. Version models or tables that external consumers depend on, and announce breaking changes with a date.
3. Enable automatic schema evolution only where it is a deliberate choice, because it lets unexpected upstream columns flow into curated tables.

## Backfill safely

1. Run the backfill on a sample or a single partition first, and compare row counts, key uniqueness and totals against expectations.
2. Write to a new table or partition set and swap it in after checks pass, so a bad backfill can be discarded instead of repaired.
3. Process bounded ranges in sequence, log progress, and make each range safe to rerun.
4. Schedule large backfills away from peak use, cap their compute, and tell downstream consumers when numbers will change.

## Handle time explicitly

1. Distinguish event time (when it happened) from processing time (when you saw it), and partition and aggregate by event time.
2. Expect late-arriving data. Reprocess a trailing window, or use watermarks, and document how late data is handled.
3. Store timestamps in UTC with their time zone, and convert only for presentation.
4. Make incremental loads overlap slightly and deduplicate, so records at window boundaries are neither lost nor doubled.

## Treat notebooks and schedules as production code

1. Move logic that runs on a schedule out of notebooks into versioned modules with tests and code review. A scheduled notebook is production code.
2. Parameterise environments and dates; never edit a notebook by hand to rerun a job.
3. Keep credentials out of notebooks and job definitions; use the platform's secret scopes or managed identities.
4. Minimise personal data in analytics: select only the columns needed, pseudonymise identifiers, apply column-level or row-level security, and make deletion requests reach derived tables and exports (see [data-and-privacy.md](data-and-privacy.md)).

## Observe freshness, volume and cost

1. Define freshness objectives for important datasets ("orders table no more than 2 hours old by 08:00 UTC") and alert on misses, including runs that never started.
2. Track row counts, rejected records, duration and cost per run, and alert on anomalies.
3. Keep lineage so you can answer "which dashboards use this column?" before changing it.
4. Prune partitions, avoid full scans in incremental models, and set limits on cluster size and query cost.

- [ ] Rerunning the job for the same period produces identical outputs.
- [ ] Key columns have uniqueness and not-null tests, and sources have freshness checks.
- [ ] Schema changes are additive or follow expand and contract, with consumers informed.
- [ ] Backfills write to a new location and are verified before swap.

## Failure modes

- Rerun jobs duplicate a day's data and double dashboard revenue.
- Renamed upstream columns load nulls for a week because only code was tested.
- Faulty in-place backfills overwrite production tables without restorable copies.
- Processing-time aggregation silently drops late mobile events.
- Shared notebooks expose embedded keys to hundreds of workspace users.

## Sources

- dbt, [Add data tests to your DAG](https://docs.getdbt.com/docs/build/data-tests), documents the generic data tests and how they evaluate.
- Delta Lake, [Table deletes, updates, and merges](https://docs.delta.io/latest/delta-update.html), documents `MERGE` and the idempotency requirement for `foreachBatch`.
- Danilo Sato, [Parallel Change](https://martinfowler.com/bliki/ParallelChange.html), applies equally to tables consumed by others.
