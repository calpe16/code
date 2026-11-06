"""Selected metric functions extracted from a private research project.

The UTC closing-boundary convention is documented in docs/METHODOLOGY.md.
Copyright 2026 Martin Calpe Blasco. All rights reserved.
"""

import pandas as pd


def completed_trades(trades: pd.DataFrame, open_positions: dict | None = None) -> pd.DataFrame:
    """Una operación por entrada; excluye posiciones con remanentes aún abiertos."""
    if trades.empty:
        return trades.copy()
    frame = trades.copy()
    frame["entered_at"] = pd.to_datetime(frame.entered_at, utc=True)
    numeric = [
        c
        for c in [
            "quantity",
            "gross_eur",
            "fees_eur",
            "funding_eur",
            "interest_eur",
            "conversion_fees_eur",
            "net_eur",
            "entry_notional_eur",
        ]
        if c in frame
    ]
    for col in numeric:
        frame[col] = frame[col].astype(float)
    group = ["venue", "symbol", "entered_at"]
    result = frame.groupby(group, as_index=False).agg({**{c: "sum" for c in numeric}, "exited_at": "max"})
    for position in (open_positions or {}).values():
        result = result.loc[
            ~(
                (result.venue == position.venue)
                & (result.symbol == position.symbol)
                & (result.entered_at == pd.Timestamp(position.opened_at))
            )
        ]
    return result.reset_index(drop=True)


def daily_returns(curve: pd.DataFrame, initial: float) -> pd.Series:
    if curve.empty:
        return pd.Series(dtype=float)
    frame = curve.copy()
    frame["timestamp"] = pd.to_datetime(frame.timestamp, utc=True)
    equity = frame.set_index("timestamp").equity_eur.astype(float).sort_index()
    # Una vela que cierra a 00:00 pertenece al día que acaba de terminar.
    # El punto inicial a medianoche es el ancla de capital, no un día adicional.
    if (
        len(equity) > 1
        and equity.index[0] == equity.index[0].normalize()
        and abs(equity.iloc[0] - initial) < 1e-8
    ):
        equity = equity.iloc[1:]
    equity.index = pd.DatetimeIndex(equity.index) - pd.Timedelta(nanoseconds=1)
    daily = equity.resample("1D").last().ffill()
    returns = daily.pct_change()
    returns.iloc[0] = daily.iloc[0] / initial - 1
    return returns.fillna(0)
