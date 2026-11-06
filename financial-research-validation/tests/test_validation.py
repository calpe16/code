from decimal import Decimal
from types import SimpleNamespace

import pandas as pd
import pytest

from research_sample.metrics import completed_trades, daily_returns
from research_sample.validation import max_drawdown, net_result, split_chronologically


def test_costs_and_fx_match_manual_arithmetic():
    assert net_result("100", "10", "5", "0.90") == Decimal("76.50")
    assert net_result("100", "10", "110", "0.90") == Decimal("-18.00")


@pytest.mark.parametrize(
    "values",
    [("1", "-1", "0", "1"), ("1", "0", "0", "0"), ("NaN", "0", "0", "1"), ("1", "0", "Infinity", "1")],
)
def test_invalid_costs_and_fx_are_rejected(values):
    with pytest.raises(ValueError):
        net_result(*values)


def test_drawdown_includes_initial_capital_and_recovery():
    assert max_drawdown([1100, 990, 1089], 1000) == pytest.approx(0.10)
    assert max_drawdown([900], 1000) == pytest.approx(0.10)
    assert max_drawdown([1000, 1100], 1000) == 0


def test_daily_closing_boundaries_do_not_add_a_day():
    curve = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=4, freq="D", tz="UTC"),
            "equity_eur": [1000, 1100, 990, 1089],
        }
    )
    assert daily_returns(curve, 1000).tolist() == pytest.approx([0.1, -0.1, 0.1])


def test_partial_exits_count_as_one_trade_and_open_residual_is_excluded():
    rows = [
        dict(
            venue="demo",
            symbol="SYNTH/EUR",
            entered_at="2024-01-01T01:00Z",
            exited_at="2024-01-01T02:00Z",
            quantity=1,
            net_eur=4,
        )
    ] * 2
    trades = pd.DataFrame(rows)
    result = completed_trades(trades)
    assert len(result) == 1 and result.net_eur.iloc[0] == 8
    position = SimpleNamespace(venue="demo", symbol="SYNTH/EUR", opened_at=pd.Timestamp("2024-01-01T01:00Z"))
    assert completed_trades(trades, {"position": position}).empty


def test_partition_boundary_and_future_changes_preserve_training_data():
    data = pd.DataFrame(
        {"timestamp": pd.date_range("2024-01-01", periods=5, freq="D"), "value": [1, 2, 3, 4, 5]}
    )
    train, test = split_chronologically(data, "2024-01-04")
    assert len(train) == 3 and len(test) == 2
    changed = data.copy()
    changed.loc[3:, "value"] = 9999
    pd.testing.assert_frame_equal(train, split_chronologically(changed, "2024-01-04")[0])


@pytest.mark.parametrize("times", [["2024-01-02", "2024-01-01"], ["2024-01-01", "2024-01-01"]])
def test_unsorted_or_duplicate_time_is_rejected(times):
    with pytest.raises(ValueError):
        split_chronologically(pd.DataFrame({"timestamp": times}), "2024-01-02")
