"""Standalone chronological long/cash research engine for one synthetic asset.

Copyright 2026 Martin Calpe Blasco. All rights reserved.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import ROUND_FLOOR, Decimal, localcontext
from random import Random

ZERO = Decimal(0)
DAY = timedelta(days=1)


def number(value, *, positive=False):
    try:
        result = Decimal(str(value))
    except ArithmeticError as exc:
        raise ValueError("Numeric amount required") from exc
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise ValueError("Finite nonnegative values required")
    return result


@dataclass(frozen=True)
class Bar:
    open_time: datetime
    open: Decimal
    close: Decimal

    def __post_init__(self):
        if (not isinstance(self.open_time, datetime) or self.open_time.tzinfo is None
                or self.open_time.utcoffset() != timedelta(0)):
            raise ValueError("UTC-aware timestamps required")
        object.__setattr__(self, "open", number(self.open, positive=True))
        object.__setattr__(self, "close", number(self.close, positive=True))

    @property
    def close_time(self):
        return self.open_time + timedelta(hours=8)


@dataclass(frozen=True)
class Costs:
    name: str = "base"
    fee_bps: Decimal = Decimal("5")
    spread_bps: Decimal = Decimal("8")
    slippage_bps: Decimal = Decimal("2")

    def __post_init__(self):
        for key in ("fee_bps", "spread_bps", "slippage_bps"):
            object.__setattr__(self, key, number(getattr(self, key)))
        if self.fee_bps >= 10000 or self.spread_bps / 2 + self.slippage_bps >= 10000:
            raise ValueError("Costs must leave positive prices and sale proceeds")

    def price(self, reference, side):
        if side not in {"buy", "sell"}:
            raise ValueError("Expected buy or sell")
        friction = (self.spread_bps / 2 + self.slippage_bps) / 10000
        return reference * (1 + friction if side == "buy" else 1 - friction)


@dataclass(frozen=True)
class Fill:
    id: str
    order_id: str
    entry_id: str
    side: str
    quantity: int
    reference: Decimal
    price: Decimal
    fee: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    signal_time: datetime
    execution_time: datetime
    reason: str


@dataclass
class Portfolio:
    cash: Decimal
    quantity: int = 0
    entry_id: str | None = None
    fills: dict[str, Fill] = field(default_factory=dict)

    def apply(self, fill):
        previous = self.fills.get(fill.id)
        if previous is not None:
            if previous != fill:
                raise ValueError("Fill identity reused with different data")
            return False
        if (not isinstance(fill.quantity, int) or isinstance(fill.quantity, bool)
                or fill.quantity <= 0 or fill.side not in {"buy", "sell"}):
            raise ValueError("Positive fill quantity and valid side required")
        for key in ("id", "order_id", "entry_id"):
            if not isinstance(getattr(fill, key), str) or not getattr(fill, key):
                raise ValueError("Stable fill, order and entry identities required")
        for key in ("reference", "price", "fee", "spread_cost", "slippage_cost"):
            number(getattr(fill, key), positive=key in {"reference", "price"})
        principal = fill.quantity * fill.price
        if fill.side == "buy":
            if self.quantity or principal + fill.fee > self.cash:
                raise ValueError("Entry exceeds cash or overlaps an existing position")
            self.cash -= principal + fill.fee
            self.quantity = fill.quantity
            self.entry_id = fill.entry_id
        else:
            if fill.quantity > self.quantity or fill.entry_id != self.entry_id:
                raise ValueError("Exit exceeds or misidentifies the held position")
            self.cash += principal - fill.fee
            self.quantity -= fill.quantity
            if not self.quantity:
                self.entry_id = None
        self.fills[fill.id] = fill
        return True


def synthetic_bars(count=180, seed=31):
    """Fixed analytic path plus seeded noise; no market data or fitted parameters."""
    with localcontext() as context:
        context.prec = 28
        return _synthetic_bars(count, seed)


def _synthetic_bars(count, seed):
    if isinstance(count, bool) or count < 2:
        raise ValueError("At least two bars required")
    rng = Random(seed)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    previous = Decimal("105.4")
    bars = []
    for index in range(count):
        opening = previous + Decimal(rng.randint(-30, 30)) / 100
        cycle = Decimal(abs(index % 48 - 24) - 12) * Decimal(".45")
        closing = Decimal(100) + Decimal(index) * Decimal(".05") + cycle + Decimal(rng.randint(-45, 45)) / 100
        bars.append(Bar(start + index * DAY, opening.quantize(Decimal(".01")),
                        closing.quantize(Decimal(".01"))))
        previous = bars[-1].close
    return bars


def validate_bars(bars):
    if len(bars) < 2:
        raise ValueError("At least two complete daily bars required")
    for i, bar in enumerate(bars):
        if not isinstance(bar, Bar):
            raise ValueError("Validated Bar records required")
        if i and bar.open_time - bars[i - 1].open_time != DAY:
            raise ValueError("Unique chronological daily bars required; missing bars are rejected")


def run_backtest(bars, costs=Costs(), *, strategy="sma", initial="10000", allocation=".80",
                 fast=5, slow=12, terminal="mark"):
    """Signal at the close, trade at the following open; no shorting or leverage."""
    with localcontext() as context:
        context.prec = 28
        return _run(bars, costs, strategy, number(initial, positive=True), number(allocation, positive=True),
                    fast, slow, terminal)


def _run(bars, costs, strategy, initial, allocation, fast, slow, terminal):
    validate_bars(bars)
    if (strategy not in {"sma", "buy_hold"} or terminal not in {"mark", "liquidate"}
            or not isinstance(fast, int) or not isinstance(slow, int) or not 0 < fast < slow or allocation > 1):
        raise ValueError("Invalid strategy, windows, terminal policy or allocation")
    portfolio = Portfolio(initial)
    audit, equity, closes = [], [], []
    pending = None
    prefix = f"{strategy}-{costs.name}"

    def execute(side, reference, when, signal_time, order_id, reason):
        price = costs.price(reference, side)
        quantity = (int((portfolio.cash * allocation / (price * (1 + costs.fee_bps / 10000)))
                        .to_integral_value(rounding=ROUND_FLOOR)) if side == "buy" else portfolio.quantity)
        if quantity <= 0:
            audit.append({"event": "risk_block", "time": when.isoformat(), "reason": "insufficient_cash"})
            return
        entry = order_id + "-entry" if side == "buy" else portfolio.entry_id
        fill = Fill(order_id + "-fill", order_id, entry, side, quantity, reference, price,
                    quantity * price * costs.fee_bps / 10000,
                    quantity * reference * costs.spread_bps / 20000,
                    quantity * reference * costs.slippage_bps / 10000,
                    signal_time, when, reason)
        portfolio.apply(fill)
        audit.append({"event": "fill", "time": when.isoformat(), "order_id": order_id,
                      "side": side, "quantity": quantity, "cash": str(portfolio.cash)})

    for i, bar in enumerate(bars):
        if strategy == "buy_hold" and i == 0:
            execute("buy", bar.open, bar.open_time, bar.open_time - timedelta(microseconds=1),
                    f"{prefix}-precommitted", "precommitted_benchmark")
        if pending is not None:
            execute(pending[0], bar.open, bar.open_time, pending[1], pending[2], "next_open")
            pending = None
        closes.append(bar.close)
        if strategy == "sma" and len(closes) >= slow:
            want_long = sum(closes[-fast:]) / fast > sum(closes[-slow:]) / slow
            if want_long != bool(portfolio.quantity):
                side = "buy" if want_long else "sell"
                pending = (side, bar.close_time, f"{prefix}-order-{i:04d}")
                audit.append({"event": "signal", "time": bar.close_time.isoformat(),
                              "side": side, "available_bars": len(closes)})
        if i == len(bars) - 1:
            if pending:
                audit.append({"event": "unfilled_terminal_signal", "time": bar.close_time.isoformat()})
                pending = None
            if terminal == "liquidate" and portfolio.quantity:
                execute("sell", bar.close, bar.close_time, bars[0].open_time - timedelta(microseconds=1),
                        f"{prefix}-scheduled-terminal", "precommitted_terminal_close")
        equity.append({"timestamp": bar.close_time.isoformat(), "cash": portfolio.cash,
                       "quantity": portfolio.quantity, "mark": bar.close,
                       "equity": portfolio.cash + portfolio.quantity * bar.close})
    fills = list(portfolio.fills.values())
    peak, drawdown = initial, ZERO
    for point in equity:
        peak = max(peak, point["equity"])
        drawdown = max(drawdown, (peak - point["equity"]) / peak)
    def total(key):
        return sum((getattr(fill, key) for fill in fills), ZERO)
    fees, spread, slippage = total("fee"), total("spread_cost"), total("slippage_cost")
    notional = sum((fill.quantity * fill.price for fill in fills), ZERO)
    final = equity[-1]["equity"]
    return {"strategy": strategy, "start": bars[0].open_time.isoformat(), "end": bars[-1].close_time.isoformat(),
            "initial_equity": initial, "final_equity": final, "net_result": final - initial,
            "cumulative_return": final / initial - 1, "max_drawdown": drawdown,
            "entries": sum(fill.side == "buy" for fill in fills),
            "completed_trades": sum(fill.side == "sell" for fill in fills), "fill_count": len(fills),
            "turnover": notional / initial, "fees": fees, "spread_cost": spread, "slippage_cost": slippage,
            "total_execution_costs": fees + spread + slippage, "ending_cash": portfolio.cash,
            "open_quantity": portfolio.quantity, "terminal_policy": terminal,
            "equity": equity, "fills": fills, "audit": audit}
