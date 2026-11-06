# Synthetic validation report

Synthetic demo data.

## Costs and currency

| Scenario | Gross quote units | Fees | Slippage | EUR per quote unit | Net EUR |
|---|---:|---:|---:|---:|---:|
| Base | 100 | 10 | 5 | 0.90 | 76.50 |
| Higher costs | 100 | 10 | 110 | 0.90 | −18.00 |

Hand checks: `(100 − 10 − 5) × 0.90 = 76.50 EUR`; `(100 − 10 − 110) × 0.90 = −18.00 EUR`. Each scenario uses one illustrative FX rate.

## Drawdown

The fixed equity path is `1000 → 1100 → 990 → 1089 → 1000`. The peak-to-trough fall is `(1100 − 990) / 1100 = 10%`. Finishing back at the initial 1,000 does not erase that loss along the way. An initial loss is measured against initial capital as well as later peaks.

## Time boundaries

Three observations fall before 4 January; two fall on or after it. The cutoff is excluded from training and included in test. This tiny partition example demonstrates one boundary rule, not a complete research evaluation or a statistical claim. Daily-close timestamps follow the separate UTC convention documented in [methodology](../docs/METHODOLOGY.md).

## Partial exits

The adapted function aggregates partial exits by entry ID when available and excludes the matching open residual. Legacy files without IDs retain the venue/symbol/time convention. The [tests](../tests/test_validation.py) show the expected grouping and exclusions.

![Cost sensitivity and drawdown from the invented examples](../media/research-overview.png)

Run `uv run python demo.py` for the JSON output. See [results.json](results.json), [the equity fixture](synthetic-equity.csv) and [cost scenarios](cost-scenarios.csv).

## Order reconciliation example

`execution_demo.py` records 3 units at €20 plus €0.30 fees, then 7 at €21 plus €0.70: `3 × 20 + 0.30 + 7 × 21 + 0.70 = €208`. Replaying the first fill leaves that total unchanged. An absent protective stop blocks entries; confirmed coverage of ten units clears that reconciliation issue.
