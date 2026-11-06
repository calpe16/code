"""Adapted project metrics; conventions and changes in docs/METHODOLOGY.md.

Copyright 2026 Martin Calpe Blasco. All rights reserved.
"""

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd


def completed_trades(
    trades: pd.DataFrame, open_positions: dict | None = None, *, identity_column: str | None = None
) -> pd.DataFrame:
    """Aggregate partial exits by entry_id when supplied; retain legacy compatibility."""
    if trades.empty:
        return trades.copy()
    frame = trades.copy()
    required = {"venue", "symbol", "entered_at", "exited_at"}
    if not required.issubset(frame):
        raise ValueError("Trade identity and entry/exit timestamps required")
    frame["entered_at"] = pd.to_datetime(frame.entered_at, utc=True)
    frame["exited_at"] = pd.to_datetime(frame.exited_at, utc=True)
    if frame[list(required)].isna().any().any() or (frame.exited_at < frame.entered_at).any():
        raise ValueError("Complete identities and ordered entry/exit timestamps required")
    identity = identity_column or ("entry_id" if "entry_id" in frame else None)
    group = ["venue", "symbol", "entered_at"]
    if identity:
        if identity not in frame or frame[identity].isna().any() or (frame[identity].astype(str).str.strip() == "").any():
            raise ValueError("Every row needs a nonempty entry identity")
        if (frame.groupby(["venue", "symbol", identity]).entered_at.nunique() > 1).any():
            raise ValueError("One entry identity has inconsistent entry timestamps")
        group.append(identity)
    numeric = [c for c in ["quantity", "gross_eur", "fees_eur", "funding_eur", "interest_eur",
        "conversion_fees_eur", "net_eur", "entry_notional_eur"] if c in frame]
    for col in numeric:
        frame[col] = pd.to_numeric(frame[col], errors="raise").astype(float)
        if not np.isfinite(frame[col]).all():
            raise ValueError("Finite trade amounts required")
    result = frame.groupby(group, as_index=False, sort=True).agg(
        {**{c: "sum" for c in numeric}, "exited_at": "max"})
    for position in (open_positions or {}).values():
        def field(name):
            return position.get(name) if isinstance(position, Mapping) else getattr(position, name, None)
        if field("venue") is None or field("symbol") is None:
            raise ValueError("Open position venue and symbol required")
        if identity:
            value = field(identity)
            if value is None:
                raise ValueError("Open positions need the same entry identity as exits")
            mask = (result.venue == field("venue")) & (result.symbol == field("symbol")) & (result[identity] == value)
        else:
            opened = pd.to_datetime(field("opened_at"), utc=True)
            if pd.isna(opened):
                raise ValueError("Open position timestamp required")
            mask = ((result.venue == field("venue")) & (result.symbol == field("symbol"))
                    & (result.entered_at == opened))
        result = result.loc[~mask]
    return result.reset_index(drop=True)


def daily_returns(
    curve: pd.DataFrame, initial: float, *, missing_days: str = "carry", initial_anchor: bool | None = None
) -> pd.Series:
    """UTC closing observations; midnight closes the prior day. Carry gaps explicitly."""
    if not math.isfinite(initial) or initial <= 0:
        raise ValueError("Finite positive initial capital required")
    if missing_days not in {"carry", "raise"}:
        raise ValueError("missing_days must be carry or raise")
    if curve.empty:
        return pd.Series(dtype=float)
    if not {"timestamp", "equity_eur"}.issubset(curve):
        raise ValueError("Timestamp and equity required")
    frame = curve.copy()
    times = pd.to_datetime(frame.timestamp, utc=True)
    if times.isna().any() or times.duplicated().any() or not times.is_monotonic_increasing:
        raise ValueError("Unique, complete, chronological timestamps required")
    values = pd.to_numeric(frame.equity_eur, errors="raise").astype(float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Finite nonnegative equity required")
    equity = pd.Series(values.to_numpy(), index=pd.DatetimeIndex(times))
    anchor = initial_anchor if initial_anchor is not None else (
        equity.index[0] == equity.index[0].normalize() and abs(equity.iloc[0] - initial) < 1e-8)
    if anchor:
        if not math.isclose(equity.iloc[0], initial, rel_tol=0, abs_tol=1e-8):
            raise ValueError("Initial anchor must equal initial capital")
        equity = equity.iloc[1:]
    if equity.empty:
        return pd.Series(dtype=float)
    equity.index -= pd.Timedelta(nanoseconds=1)
    daily = equity.resample("1D").last()
    gaps = daily.index[daily.isna()]
    if len(gaps) and missing_days == "raise":
        raise ValueError("Missing daily closes")
    daily = daily.ffill()
    if (daily.shift(1) == 0).any():
        raise ValueError("A return after zero equity is undefined")
    result = daily.pct_change(fill_method=None)
    result.iloc[0] = daily.iloc[0] / initial - 1
    result.attrs["carried_days"] = tuple(gaps.strftime("%Y-%m-%d"))
    return result
