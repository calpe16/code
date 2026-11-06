from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, getcontext

import pytest

from research_sample.backtest import Bar, Costs, Portfolio, run_backtest, synthetic_bars


def bars(opens, closes):
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [Bar(start + timedelta(days=i), str(a), str(b)) for i, (a, b) in enumerate(zip(opens, closes))]


ZERO = Costs("zero", 0, 0, 0)


def test_signal_close_executes_only_at_next_open_with_hand_calculated_result():
    result = run_backtest(bars([10, 11, 13, 6], [10, 12, 8, 7]), ZERO,
                          initial="100", allocation="1", fast=1, slow=2)
    buy, sell = result["fills"]
    assert (buy.quantity, buy.price, sell.price) == (7, 13, 6)
    assert buy.signal_time < buy.execution_time and sell.signal_time < sell.execution_time
    assert buy.entry_id == sell.entry_id
    assert result["final_equity"] == 51 and result["net_result"] == -49
    assert result["max_drawdown"] == Decimal(".49")


def test_fees_use_executed_notional_and_open_positions_are_marked():
    data = bars([100, 110, 90], [100, 110, 90])
    result = run_backtest(data, Costs("fee", 100, 0, 0), strategy="buy_hold", initial="1000", allocation="1")
    assert result["open_quantity"] == 9 and result["ending_cash"] == 91
    assert result["fees"] == 9 and result["final_equity"] == 901
    assert result["max_drawdown"] == pytest.approx(Decimal(180) / Decimal(1081))
    assert result["completed_trades"] == 0
    closed = run_backtest(data, Costs("fee", 100, 0, 0), strategy="buy_hold",
                          initial="1000", allocation="1", terminal="liquidate")
    assert closed["fees"] == Decimal("17.1") and closed["final_equity"] == Decimal("892.9")
    assert closed["turnover"] == Decimal("1.71") and closed["open_quantity"] == 0


def test_spread_and_slippage_are_in_price_and_never_charged_twice():
    result = run_backtest(bars([100, 100], [100, 100]), Costs("toy", 10, 20, 10),
                          strategy="buy_hold", initial="201", allocation="1")
    fill = result["fills"][0]
    assert fill.quantity == 2 and fill.price == Decimal("100.2")
    assert fill.fee == Decimal(".2004")
    assert fill.spread_cost == Decimal(".2") and fill.slippage_cost == Decimal(".2")
    assert result["final_equity"] == Decimal("200.3996")
    assert result["total_execution_costs"] == Decimal(".6004")
    assert Costs("toy", 10, 20, 10).price(Decimal(100), "sell") == Decimal("99.8")


def test_future_prices_do_not_change_prior_signals_fills_or_equity():
    data = synthetic_bars()
    cutoff = 80
    changed = data[:cutoff] + [replace(bar, open=bar.open * 2, close=bar.close * 2) for bar in data[cutoff:]]
    original, altered = run_backtest(data), run_backtest(changed)
    end = data[cutoff - 1].close_time
    assert original["equity"][:cutoff] == altered["equity"][:cutoff]
    assert [f for f in original["fills"] if f.execution_time <= end] == [
        f for f in altered["fills"] if f.execution_time <= end]
    assert [e for e in original["audit"] if e["time"] <= end.isoformat()] == [
        e for e in altered["audit"] if e["time"] <= end.isoformat()]


def test_final_signal_cannot_create_a_same_close_fill():
    result = run_backtest(bars([10, 10, 10], [10, 9, 12]), ZERO, fast=1, slow=2)
    assert not result["fills"]
    assert result["audit"][-1]["event"] == "unfilled_terminal_signal"


def test_equity_cash_position_and_cost_identities_hold_at_every_close():
    data = synthetic_bars()
    result = run_backtest(data)
    cash = result["initial_equity"]
    quantity = 0
    for point in result["equity"]:
        for fill in result["fills"]:
            if fill.execution_time.isoformat()[:10] == point["timestamp"][:10]:
                cash += (-fill.quantity * fill.price - fill.fee if fill.side == "buy"
                         else fill.quantity * fill.price - fill.fee)
                quantity += fill.quantity if fill.side == "buy" else -fill.quantity
        assert cash == point["cash"] and cash >= 0
        assert quantity == point["quantity"] and quantity >= 0
        assert point["equity"] == cash + quantity * point["mark"]
    assert len({f.id for f in result["fills"]}) == result["fill_count"]
    assert len({f.entry_id for f in result["fills"] if f.side == "buy"}) == result["entries"]
    assert result["total_execution_costs"] == result["fees"] + result["spread_cost"] + result["slippage_cost"]


def test_benchmark_and_strategy_use_exactly_the_same_horizon_and_cash():
    data = synthetic_bars()
    strategy = run_backtest(data)
    benchmark = run_backtest(data, strategy="buy_hold")
    assert (strategy["start"], strategy["end"], strategy["initial_equity"]) == (
        benchmark["start"], benchmark["end"], benchmark["initial_equity"])
    assert [p["timestamp"] for p in strategy["equity"]] == [p["timestamp"] for p in benchmark["equity"]]
    assert benchmark["entries"] == 1 and benchmark["completed_trades"] == 0


def test_replay_fill_is_idempotent_and_conflicting_identity_is_rejected():
    result = run_backtest(bars([100, 100], [100, 100]), ZERO, strategy="buy_hold")
    fill = result["fills"][0]
    portfolio = Portfolio(Decimal("10000"))
    portfolio.apply(fill)
    assert not portfolio.apply(fill)
    with pytest.raises(ValueError, match="identity"):
        portfolio.apply(replace(fill, price=fill.price + 1))


def test_invalid_economics_or_over_exit_do_not_mutate_the_portfolio():
    result = run_backtest(bars([100, 100], [100, 100]), ZERO, strategy="buy_hold")
    fill = result["fills"][0]
    portfolio = Portfolio(Decimal("10000"))
    with pytest.raises(ValueError):
        portfolio.apply(replace(fill, fee=Decimal("-1")))
    assert portfolio.cash == 10000 and portfolio.quantity == 0
    portfolio.apply(fill)
    old_cash = portfolio.cash
    with pytest.raises(ValueError):
        portfolio.apply(replace(fill, id="exit", side="sell", quantity=fill.quantity + 1))
    assert portfolio.cash == old_cash and portfolio.quantity == fill.quantity


def test_equivalent_experiments_are_deterministic_with_independent_decimal_context():
    first = run_backtest(synthetic_bars())
    old = getcontext().prec
    try:
        getcontext().prec = 6
        # Reuse the identical input; generation has a fixed context too.
        second = run_backtest(synthetic_bars())
    finally:
        getcontext().prec = old
    assert first == second


@pytest.mark.parametrize("data", [[], [Bar(datetime(2024, 1, 1, tzinfo=timezone.utc), 1, 1)],
    bars([1, 2, 3], [1, 2, 3])[::2], bars([1, 2], [1, 2])[::-1],
    [Bar(datetime(2024, 1, 1, tzinfo=timezone.utc), 1, 1)] * 2])
def test_missing_duplicate_or_unordered_data_is_rejected(data):
    with pytest.raises(ValueError):
        run_backtest(data)


@pytest.mark.parametrize("price", [None, "NaN", "Infinity", "0", "-1"])
def test_incomplete_and_invalid_prices_fail(price):
    with pytest.raises(ValueError):
        Bar(datetime(2024, 1, 1, tzinfo=timezone.utc), price, 1)


def test_cash_limits_prevent_an_unaffordable_entry():
    result = run_backtest(bars([100, 100], [100, 100]), strategy="buy_hold", initial="1")
    assert not result["fills"] and result["audit"][0]["event"] == "risk_block"


@pytest.mark.parametrize("kwargs", [{"initial": "0"}, {"allocation": "1.1"},
    {"fast": 3, "slow": 2}, {"terminal": "guess"}])
def test_invalid_experiment_configuration_fails(kwargs):
    with pytest.raises(ValueError):
        run_backtest(synthetic_bars(), **kwargs)
