# Source provenance

## Adapted application code

Selected from the private Brújula application on 6 November 2026:

| Source | Portfolio component | Changes in this revision |
|---|---|---|
| `lib/domain/finance.dart` | `moneyCents` in `lib/finance_review.dart` | Validate original signs and grouping; use BigInt before enforcing the safe-cent limit. |
| `lib/domain/import_review.dart` | Import-review types and matching | Enforce one-to-one stored matches, deterministic candidates, explicit repeated-reference/ID conflicts and non-null source rows. |
| `lib/domain/model.dart` | JSON alias and text normalization | Retain the small helpers needed by the extraction. |

## Standalone synchronization model

`lib/sync_demo.dart` is a new model, based on the inspected flows in `lib/services/store.dart` (`upsert`, `markSent`, `reconcile`, `resolve`), version comparison in `cloud/Core.js`, and receipt handling in the cloud service. It is not a literal extraction. It replaces platform persistence with JSON snapshots, the transport with direct calls, and the app's entity collection with one generic fictional record. The model binds operation IDs to canonical content as an additional demonstration guard.

## Visual material

The product tour uses the app's actual Flutter widgets with a fresh in-memory fixture. The home view retains the full app shell; most module views use an outer capture frame. There are 12 desktop and three phone-width renders in the expanded tour, plus three earlier financial renders with a separate fixture. The fixtures contain invented records rather than anonymized personal data. The sync diagram is explanatory; the older import illustrations and GIF visualize the CLI outcomes.
