# Methodology

[Back to the project](../README.md)

## Standalone backtest and experiment

`backtest.py` is a new independent long/cash engine. Its moving-average rule and published synthetic generator were chosen for this demonstration, without extracting the private strategy. It uses one asset, no leverage and whole units. An entry allocates 80% of available cash including its fee budget; this is an entry-sizing rule, not a continuously enforced portfolio-weight cap.

Each artificial bar opens in UTC and closes eight hours later. Signals see only closes already processed, then execute at the next daily open. Missing, duplicate or unordered bars fail validation. The last signal has no next bar and remains unfilled. The passive reference is precommitted before the first open, over the same full horizon including the strategy's cash-only warm-up.

The reference shares the initial capital, entry budget, period, costs and terminal policy. Its continuous exposure differs from the strategy's intermittent positions; it is not an exposure-matched comparison.

The full quoted spread contributes half to each side; adverse slippage is added to the buy price or subtracted from the sell price. Fees use executed notional. These price effects are recorded as friction for analysis, and never debited again. Decimal arithmetic uses precision 28; fees retain fractional cents. This is a stated simulation convention rather than a currency-settlement rule.

Default final equity includes remaining units marked at the last close. Their gain is unrealized. The optional `terminal='liquidate'` policy schedules a final-close sale in advance and includes its costs; use the same policy for the benchmark. Maximum drawdown is sampled at closes and includes initial capital. Completed trades are full round trips; turnover is both-side executed notional divided by initial capital. Scenario and model names scope exported order and entry identities.

The fixed artificial cycles make this rule favourable. No market-data calibration, statistical edge or annualized performance is inferred. Whole-unit affordability can change sizes between cost cases. `backtest_demo.py --check` compares the regenerated data, event log, fills, equity, summary and report; plotting converts values to floats only for display.

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


The incident model's gate is scoped to a single order. It reserves that case while the order is open or partial, blocks on uncertain/invalid observations and requires fresh reconciliation after restart. A matching new observation can clear a reconciliation issue; contradictory fill or response identities retain a persistent halt. It does not calculate aggregate exposure across multiple positions. Acquisition accounting separates executed principal, fees and their total.
