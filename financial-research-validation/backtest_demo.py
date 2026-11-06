"""Generate or check the fixed synthetic research experiment and its artefacts."""
import argparse
import csv
import hashlib
import io
import json
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from research_sample.backtest import Costs, run_backtest, synthetic_bars

METRICS = ["initial_equity", "final_equity", "net_result", "cumulative_return", "max_drawdown",
           "entries", "completed_trades", "fill_count", "turnover", "fees", "spread_cost",
           "slippage_cost", "total_execution_costs", "ending_cash", "open_quantity", "terminal_policy"]
DATA_FILES = ["dataset.csv", "equity.csv", "fills.csv", "summary.csv", "summary.json", "events.json", "REPORT.md"]


def json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def csv_text(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def experiment():
    bars = synthetic_bars(180, 31)
    dataset = csv_text([{"open_time": bar.open_time.isoformat(), "open": bar.open, "close": bar.close}
                        for bar in bars])
    scenarios = [Costs("zero", 0, 0, 0), Costs("base", 5, 8, 2),
                 Costs("stress", 15, 20, 20), Costs("high", 30, 40, 50)]
    cases = []
    for costs in scenarios:
        strategy = run_backtest(bars, costs)
        benchmark = run_backtest(bars, costs, strategy="buy_hold")
        cases.append({"scenario": costs.name, "costs": costs, "strategy": strategy,
                      "benchmark": benchmark,
                      "excess_return": strategy["cumulative_return"] - benchmark["cumulative_return"]})
    return dataset, cases


def generate(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    dataset, cases = experiment()
    dataset_hash = hashlib.sha256(dataset.encode()).hexdigest()
    summary = {"data": "Synthetic demo data", "dataset_sha256": dataset_hash,
               "settings": {"seed": 31, "bars": 180, "fast": 5, "slow": 12, "initial_eur": "10000",
                            "cash_allocation": "0.80", "terminal": "mark", "decimal_precision": 28},
               "start": cases[0]["strategy"]["start"], "end": cases[0]["strategy"]["end"], "scenarios": []}
    equity, fills, flat, events = [], [], [], {}
    for case in cases:
        name = case["scenario"]
        row = {"scenario": name, "costs": asdict(case["costs"]), "excess_return": case["excess_return"]}
        for model in ("strategy", "benchmark"):
            run = case[model]
            row[model] = {key: run[key] for key in METRICS}
            flat.append({"scenario": name, "model": model, **row[model]})
            equity.extend({"scenario": name, "model": model, **point} for point in run["equity"])
            fills.extend({"scenario": name, "model": model, **asdict(fill)} for fill in run["fills"])
            events[f"{name}/{model}"] = run["audit"]
        summary["scenarios"].append(row)
    for name, text in {"dataset.csv": dataset, "equity.csv": csv_text(equity), "fills.csv": csv_text(fills),
                       "summary.csv": csv_text(flat), "summary.json": json.dumps(summary, default=json_default,
                           indent=2, sort_keys=True) + "\n", "events.json": json.dumps(events, indent=2, sort_keys=True) + "\n"}.items():
        (output / name).write_text(text, encoding="utf-8", newline="\n")
    lines = ["# Reproducible backtesting experiment", "", "Synthetic demo data.", "",
             "Question: how does a fixed long/cash moving-average rule change when execution costs increase?",
             "", "180 artificial daily bars, seed 31, 5/12 close-based averages, €10,000 initial cash and 80% cash allocation.",
             "Signals execute at the next open. The passive reference buys once at the first open with the same allocation,",
             "cost scenario and horizon. Ending holdings are marked at the last close, with no assumed exit fee.", "",
             "## Performance", "",
             "| Scenario | Return | Max DD | Net EUR | Passive return | Difference pp |",
             "|---|---:|---:|---:|---:|---:|"]
    for case in cases:
        r, b, c = case["strategy"], case["benchmark"], case["costs"]
        lines.append(f"| {c.name} | {r['cumulative_return']:.2%} | {r['max_drawdown']:.2%} | {r['net_result']:.2f} | "
            f"{b['cumulative_return']:.2%} | {case['excess_return'] * 100:.2f} |")
    lines += ["", "## Activity and cost assumptions", "",
              "| Scenario | Fee / spread / slippage bps | Completed / open | Turnover | Execution costs EUR |",
              "|---|---|---|---:|---:|"]
    for case in cases:
        r, c = case["strategy"], case["costs"]
        lines.append(f"| {c.name} | {c.fee_bps} / {c.spread_bps} / {c.slippage_bps} | "
                     f"{r['completed_trades']} / {int(r['open_quantity'] > 0)} | "
                     f"{r['turnover']:.3f} | {r['total_execution_costs']:.2f} |")
    lines += ["", "Spread is the full quoted spread; each fill pays half plus adverse slippage. Fees use executed notional.",
              "Spread/slippage are already in fill prices and are not debited a second time. Total execution costs are",
              "fees plus spread and slippage impact. Turnover is both-side executed notional divided by initial capital.",
              "Max DD uses close-sampled equity and initial capital; it does not describe an unobserved intraday path.",
              "Completed counts full round trips; open counts the remaining entry. Whole-unit affordability can alter sizes between cost scenarios.",
              "", "Dataset SHA-256:", "", "```text", dataset_hash, "```", "",
              "[Full precision results](summary.json) · [Data](dataset.csv) · [Fills](fills.csv) · [Equity](equity.csv) · [Events](events.json)",
              "", "![Generated cost experiment](cost-experiment.png)", "",
              "All values above are generated by `backtest_demo.py`. Windows and cost cases are fixed demonstration choices,",
              "not a calibrated strategy or an estimate of actual execution costs. Missing daily bars fail validation.",
              "Use `terminal='liquidate'` in the API to model a precommitted final-close sale for both models, including its friction."]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    plot_cases(cases, output / "cost-experiment.png")
    return summary


def plot_cases(cases, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5.2), dpi=150)
    fig.patch.set_facecolor("#f1f5f2")
    fig.suptitle("A fixed rule under four execution-cost assumptions", x=.06, ha="left", fontsize=17, weight="bold")
    fig.text(.06, .87, "Synthetic demo data · generated from the same 180-bar path", color="#5a6c61")
    fig.subplots_adjust(left=.07, right=.97, top=.73, bottom=.21, wspace=.3)
    colors = ["#246b55", "#569a7c", "#b4864c", "#a34f43"]
    for case, color in zip(cases, colors, strict=True):
        a.plot([(float(p["equity"] / 10000) - 1) * 100 for p in case["strategy"]["equity"]],
               label=case["scenario"], color=color, lw=1.7)
    a.plot([(float(p["equity"] / 10000) - 1) * 100 for p in cases[1]["benchmark"]["equity"]],
           label="passive / base costs", color="#657b99", ls="--", lw=1.5)
    a.set(xlabel="Artificial daily observation", ylabel="Cumulative return %", title="Closing equity after costs")
    a.legend(fontsize=8)
    positions = range(len(cases))
    b.bar(positions, [float(c["strategy"]["net_result"]) for c in cases], color=colors)
    b.axhline(0, color="#8c9b93", lw=.8)
    b.set_xticks(list(positions), [c["scenario"] for c in cases])
    b.set(ylabel="Net result EUR", title="Same data and rule; different friction")
    for i, case in enumerate(cases):
        value = float(case["strategy"]["net_result"])
        b.annotate(f"€{value:,.0f}", (i, value), xytext=(0, 5 if value >= 0 else -13),
                   textcoords="offset points", ha="center", fontsize=9)
    fig.text(.06, .06, "No future prices enter the signal. Open final holdings are marked; no terminal sale is assumed.", fontsize=9, color="#5a6c61")
    fig.savefig(path, facecolor=fig.get_facecolor(), metadata={"Software": "Reproducible backtest demo"})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "examples/backtest")
    parser.add_argument("--check", action="store_true", help="Recompute and compare committed numerical artefacts")
    args = parser.parse_args()
    if args.check:
        with TemporaryDirectory() as folder:
            result = generate(folder)
            for filename in DATA_FILES:
                if (Path(folder) / filename).read_bytes() != (args.output / filename).read_bytes():
                    raise RuntimeError(f"Reproducibility check failed: {filename}")
    else:
        result = generate(args.output)
    print(json.dumps({"dataset_sha256": result["dataset_sha256"], "scenarios": len(result["scenarios"]),
                      "reproducibility_check": args.check}, indent=2))


if __name__ == "__main__":
    main()
