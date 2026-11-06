# Research decisions and limits

## Separate the question from the attractive chart

The private project compares hypotheses against costs and passive references, records failed
variants, and separates development from reserved evaluation. A profitable backtest is not
proof of a repeatable advantage. Data gaps, selection over many variants, FX and the difference
between simulated and actual fills all affect the conclusion.

## A rejected research direction

One global asset-allocation hypothesis improved a particular falling-market period but lagged
the global passive reference over the examined full sample. Lowering assumed costs did not
resolve that comparison, so it was not promoted. This is a documented private research outcome,
not an independently reproduced public experiment. The data and complete selection logic are
not redistributed here. The public synthetic cost example illustrates a separate validation principle.

## Conventions in the public sample

- `daily_returns` is extracted from the project. Observations are equity at the close of the
  represented interval in UTC; a point at midnight belongs to the day just completed.
  An initial midnight anchor is excluded from the daily-return count. Missing days are forward-filled;
  the function is not a market-data-quality validator. The demo deliberately has no missing days.
- `completed_trades` aggregates partial exits by venue, symbol and entry timestamp. It assumes
  there is not more than one independent entry with that identity; open residuals are excluded.
- Cost/FX arithmetic uses Decimal. A single fixed FX rate is used for each illustrative scenario;
  it does not model a multicurrency cash ledger or intraday conversions.
- The drawdown helper measures against both the initial capital and subsequent peaks. The
  chronological helper excludes the cutoff from training and includes it in test.

The last two helpers are new portfolio adapters inspired by the private project, not verbatim
production functions. No Sharpe ratio, annualized synthetic return or statistical significance is claimed.

## Current boundary

The private project's sustainable live advantage has not been demonstrated. Native operational
acceptance and prospective observation remain incomplete. This sample does not connect to it,
activate it, expose current strategy parameters or certify the safety of real-money execution.
