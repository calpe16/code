# Source and adaptations

The sample was extracted on 6 November 2026 from my private Brújula application.

| Private source | Published selection | Adaptation |
|---|---|---|
| `lib/domain/finance.dart` | `moneyCents` | Original financial conversion logic retained. |
| `lib/domain/import_review.dart` | `ImportMatch`, `ReviewedImportRow`, `reviewImport` and comparison helpers | Imports removed; the rest of the app is excluded. |
| `lib/domain/model.dart` | `Json` alias and `normalize` | No full personal-record model or timezone layer. |

Tests, demo fixtures, presentation images and documentation were newly prepared with AI assistance
for this sample. They use fictional records, not anonymized real transactions. Formatting changes
may differ from the private source. This repository does not establish independent authorship of
every generated line or a professional skill level.
