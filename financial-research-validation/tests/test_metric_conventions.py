import pandas as pd
import pytest

from research_sample.metrics import completed_trades, daily_returns


def curve(times, values):
    return pd.DataFrame({"timestamp": times, "equity_eur": values})


def test_gaps_are_carried_and_reported_or_rejected_explicitly():
    data = curve(["2026-01-01T00:00Z", "2026-01-02T00:00Z", "2026-01-04T00:00Z"], [100, 110, 121])
    result = daily_returns(data, 100)
    assert result.tolist() == pytest.approx([.1, 0, .1])
    assert result.attrs["carried_days"] == ("2026-01-02",)
    with pytest.raises(ValueError, match="Missing daily"):
        daily_returns(data, 100, missing_days="raise")


def test_empty_curve_and_single_initial_anchor_have_no_return():
    assert daily_returns(pd.DataFrame(), 100).empty
    assert daily_returns(curve(["2026-01-01"], [100]), 100).empty


def test_explicit_real_first_close_is_not_removed_as_an_anchor():
    result = daily_returns(curve(["2026-01-02", "2026-01-03"], [100, 110]), 100, initial_anchor=False)
    assert result.tolist() == pytest.approx([0, .1])
    assert str(result.index[0].date()) == "2026-01-01"


def test_irregular_observations_use_last_close_within_each_utc_day():
    data = curve(["2026-01-01T09:00Z", "2026-01-01T17:00Z", "2026-01-02T00:00Z", "2026-01-02T17:00Z"], [102, 105, 110, 99])
    assert daily_returns(data, 100).tolist() == pytest.approx([.1, -.1])


@pytest.mark.parametrize("times", [["2026-01-02", "2026-01-01"], [None, "2026-01-02"]])
def test_unsorted_or_incomplete_times_fail(times):
    with pytest.raises(ValueError):
        daily_returns(curve(times, [100, 110]), 100)


def test_total_loss_allowed_but_return_after_zero_is_undefined():
    assert daily_returns(curve(["2026-01-02"], [0]), 100).tolist() == [-1]
    with pytest.raises(ValueError, match="after zero"):
        daily_returns(curve(["2026-01-02", "2026-01-03"], [0, 10]), 100)


def trades():
    return pd.DataFrame([dict(venue="demo",symbol="SYNTH",entry_id=entry,
        entered_at="2026-01-01",exited_at=exit,quantity=1,net_eur=net)
        for entry,exit,net in [("a","2026-01-02",3),("a","2026-01-03",4),("b","2026-01-03",5)]])


def test_partial_exits_group_by_entry_and_only_matching_open_residual_is_excluded():
    result = completed_trades(trades(), {"a":dict(venue="demo",symbol="SYNTH",entry_id="a")})
    assert len(result) == 1 and result.entry_id.iloc[0] == "b" and result.net_eur.iloc[0] == 5
    result = completed_trades(trades())
    assert result.loc[result.entry_id == "a", "net_eur"].iloc[0] == 7


def test_identity_mode_rejects_missing_ids_and_inconsistent_entry_time():
    data = trades()
    data.loc[0,"entry_id"] = None
    with pytest.raises(ValueError):
        completed_trades(data)
    data = trades()
    data.loc[0,"entered_at"] = "2025-12-31"
    with pytest.raises(ValueError, match="inconsistent"):
        completed_trades(data)
    with pytest.raises(ValueError, match="same entry identity"):
        completed_trades(trades(), {"a":dict(venue="demo",symbol="SYNTH")})
