import pandas as pd
import pytest

from research_sample.metrics import completed_trades, daily_returns


def trade_rows():
    return pd.DataFrame([
        dict(venue="demo", symbol="SYNTH/EUR", entered_at="2026-01-01T00:00Z",
             exited_at="2026-01-02T00:00Z", entry_id=entry, quantity=1, net_eur=value)
        for entry, value in [("entry-a", 3), ("entry-b", 7)]
    ])


def test_independent_entries_at_the_same_timestamp_remain_separate():
    result = completed_trades(trade_rows())
    assert len(result) == 2
    assert sorted(result.net_eur.tolist()) == [3, 7]


@pytest.mark.parametrize("initial", [0, -1, float("nan"), float("inf")])
def test_invalid_initial_capital_is_rejected(initial):
    with pytest.raises(ValueError):
        daily_returns(pd.DataFrame({"timestamp": ["2026-01-01"], "equity_eur": [100]}), initial)


@pytest.mark.parametrize("values", [[None, 100], [100, float("inf")], [100, -1]])
def test_invalid_equity_is_rejected(values):
    with pytest.raises(ValueError):
        daily_returns(pd.DataFrame({"timestamp": ["2026-01-01", "2026-01-02"],
                                    "equity_eur": values}), 100)


def test_duplicate_timestamps_are_not_silently_collapsed():
    with pytest.raises(ValueError):
        daily_returns(pd.DataFrame({"timestamp": ["2026-01-02"] * 2,
                                    "equity_eur": [100, 110]}), 100)
