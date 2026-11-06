# Technical notes

[Back to Brújula](../README.md)

## Import review

`moneyCents` validates the original token layout before conversion. It accepts one edge sign or a pair of accounting parentheses, one optional currency annotation, European/US separators and properly grouped spaces. A single separator followed by three digits denotes thousands; fractions have one or two digits. The maximum is 9,007,199,254,740,991 cents, matching safe integer storage across the app's Dart/JavaScript boundary. Sub-cent values and malformed grouping are rejected.

`reviewImport` keeps the imported source values separate from later classification edits. Its decisions follow this order:

1. Validate unique stored IDs and flag repeated incoming IDs or incompatible ID collisions.
2. Match an actual source-file/table/component/row identity when present. Missing row values never establish identity.
3. Match a bank reference within its account. A reference repeated in the incoming file or with multiple stored candidates requires review as a conflict, unless a specific source row resolves the identity.
4. Consume each matched stored record once. Similarity without identity produces a possible match, using a stable ID order when several old purchases look alike.
5. Keep distinct unreferenced rows from the same statement as separate purchases. Repeating a specific source row is handled as a reimport.

A conflict leaves the row available for a decision. It does not delete, merge or post it. Repeated reference alone is treated conservatively because the fixture cannot tell whether the bank reused a reference or a row was copied twice. The [tests](../test/import_cases_test.dart) document those choices.

## Synchronization

The complete app has a local working copy, pending operations and remote confirmed records. The new standalone model isolates that workflow for one record:

| Event | Result |
|---|---|
| Edit before sending | Coalesce unsent changes against their original base version. |
| Edit after sending | Retain a separate operation for the subsequent edit. |
| Matching server version | Apply once and increment the version. |
| Lost response | Retry the same operation identity; return its stored receipt. |
| Operation ID reused with other content | Reject the identity collision. |
| Version conflict | Retain local content and remote content separately. |
| Keep local | Rebase as a new operation; another intervening edit can conflict again. |
| Accept remote | Discard the queued edit and use the confirmed record. |

Pending changes are cleared only when a matching receipt has a sufficiently new confirmed record, or when a conflict is already satisfied by that record. JSON snapshots preserve in-flight operations and server receipts across a simulated restart. Snapshot serialization is exercised locally; the full app's filesystem, authentication and transport are separate components.

## Reading the product tour

The gallery's classified spending is `650 + 190 + 45 − 25 = €860`; a €300 transfer stays separate. The two priced holdings gain `200 − 20 = €180`; an unknown asset value stays unknown. An 8/10 assignment covering 40% of a course is a partial grade while the remaining exam is pending. Two planned recipes need `2 × 160 − 100 = 220 g` of rice after stock; tomatoes in pieces are not converted to grams without a conversion. The food diary chooses either its 1,100 kcal item total or the separate 2,100 kcal manual total.

These gallery calculations describe the full app's rendered views. The runnable code here covers import review and the standalone sync model. Connected integrations and the complete app source remain private.
