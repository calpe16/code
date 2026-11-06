# Methodology

[Back to the project](../README.md)

## Research workflow

The wider platform compares hypotheses with passive references, records unsuccessful variants and separates development from reserved evaluation. It includes continuous historical portfolio paths and rising/falling/sideways period diagnostics. Those period labels describe history; they are not predictive signals.

One global allocation hypothesis improved a particular falling-market interval but lagged the passive reference over the examined full sample. Lowering assumed costs did not resolve the comparison, so it was not promoted. This decision is documented in the private project; the complete market dataset and selection process remain private. Data gaps, variant selection, costs, FX and actual fills all affect interpretation. Sustainable live advantage, prospective observation and operational acceptance remain unestablished.

## Daily returns

`daily_returns` accepts finite nonnegative equity and positive initial capital, with unique timestamps in ascending order. Missing or duplicate observations fail explicitly. Each timestamp is an interval close in UTC: a close at midnight belongs to the previous day. Irregular intraday observations use the last close within the day.

The default anchor convention removes a first midnight observation equal to initial capital. `initial_anchor=False` retains such an observation when it is an actual first close; `True` explicitly marks an anchor. A lone anchor yields no return. Empty input yields an empty series after capital validation.

To preserve the earlier convention, missing calendar days carry the last close by default, producing zero return on those days. The resulting Series lists them in `attrs['carried_days']`. Use `missing_days='raise'` to require daily coverage. Carrying is a stated assumption, not an observed unchanged market value. A total loss can yield −100%; a subsequent percentage return from zero equity is undefined and rejected.

## Partial exits and identity

`completed_trades` uses `entry_id` when supplied, or an explicit `identity_column`. Partial exits for one entry are summed; independent entries at the same timestamp stay separate. Open residuals exclude only the matching entry identity. Entry/exit timestamps and financial amounts are validated.

Older project records without an entry ID retain grouping by venue, symbol and entry time for compatibility. Two independent entries with exactly that legacy identity cannot be distinguished from those fields alone. Supply a stable entry ID rather than guessing. In identity mode, open positions must carry the same ID.

## Costs, drawdown and partitions

The cost example uses Decimal and one fixed FX rate per scenario. It is not a multicurrency cash ledger. Drawdown measures losses against initial capital and later peaks. The chronological helper excludes the cutoff from training and includes it in test. These small checks verify those conventions; they do not establish statistical significance or settle the evaluation of the wider strategy.

## Simulated execution

`execution.py` models one long entry in a fictional instrument. It records submission state before a supplied response, preserves `UNKNOWN` until reconciliation and deduplicates fills by identity and economics. Reusing a fill identity with other values or overfilling an order creates a persistent halt. A rejected order also retains a halt.

Reconciliation compares the fill ledger with supplied cumulative fills and position quantity, checks the order state and requires confirmed stop coverage equal to the open position. Open/partial orders keep the entry reservation. A cancellation retains any filled position. Reconciliation issues can clear on a subsequent matching observation; persistent identity/order faults remain blocked. Restoring a snapshot requires a new reconciliation.

This is a standalone model of the inspected control flow. Remote observations are function arguments; the example excludes transport, market signals, sizing policy, live stop placement and venue-specific execution. The actual dashboard tour uses an independent synthetic ledger, so its status values need not match this scenario.
