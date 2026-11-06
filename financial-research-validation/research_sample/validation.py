"""Small validation boundary added for the public sample; no trading signals."""

import math
from decimal import Decimal

import pandas as pd


def net_result(gross_quote: str, fees_quote: str, slippage_quote: str, fx_quote_eur: str) -> Decimal:
    values = [Decimal(x) for x in (gross_quote, fees_quote, slippage_quote, fx_quote_eur)]
    if not all(x.is_finite() for x in values):
        raise ValueError("Finite amounts are required")
    gross, fees, slippage, fx = values
    if min(fees, slippage) < 0 or fx <= 0:
        raise ValueError("Costs must be nonnegative and FX positive")
    return (gross - fees - slippage) * fx


def max_drawdown(equity: list[float], initial: float) -> float:
    if not math.isfinite(initial) or initial <= 0 or not equity:
        raise ValueError("Positive initial capital and observations required")
    peak = initial
    worst = 0.0
    for value in equity:
        if not math.isfinite(value) or value < 0:
            raise ValueError("Finite nonnegative equity required")
        peak = max(peak, value)
        worst = max(worst, 1 - value / peak)
    return worst


def split_chronologically(frame: pd.DataFrame, cutoff: str):
    ordered = frame.copy()
    ordered["timestamp"] = pd.to_datetime(ordered.timestamp, utc=True)
    if ordered.timestamp.duplicated().any() or not ordered.timestamp.is_monotonic_increasing:
        raise ValueError("Expected unique, chronological observations")
    boundary = pd.Timestamp(cutoff)
    boundary = boundary.tz_localize("UTC") if boundary.tzinfo is None else boundary.tz_convert("UTC")
    train = ordered.loc[ordered.timestamp < boundary].copy()
    test = ordered.loc[ordered.timestamp >= boundary].copy()
    if train.empty or test.empty:
        raise ValueError("Both partitions need observations")
    return train, test
