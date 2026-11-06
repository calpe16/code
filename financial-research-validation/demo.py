"""Reproducible synthetic checks; no market downloads, broker or credentials."""

import csv
import json
from pathlib import Path

import pandas as pd

from research_sample.metrics import daily_returns
from research_sample.validation import max_drawdown, net_result, split_chronologically


def main():
    target = Path(__file__).parent / "examples"
    target.mkdir(exist_ok=True)
    curve = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC"),
            "equity_eur": [1000.0, 1100.0, 990.0, 1089.0, 1000.0],
        }
    )
    train, test = split_chronologically(curve, "2024-01-04")
    scenarios = [
        {
            "scenario": "base",
            "gross_quote": "100",
            "fees_quote": "10",
            "slippage_quote": "5",
            "fx_quote_eur": "0.90",
        },
        {
            "scenario": "higher costs",
            "gross_quote": "100",
            "fees_quote": "10",
            "slippage_quote": "110",
            "fx_quote_eur": "0.90",
        },
    ]
    for row in scenarios:
        row["net_eur"] = str(
            net_result(*(row[k] for k in ("gross_quote", "fees_quote", "slippage_quote", "fx_quote_eur")))
        )
    result = {
        "data": "SYNTHETIC - not investment performance",
        "daily_returns": daily_returns(curve, 1000).tolist(),
        "max_drawdown": max_drawdown(curve.equity_eur.tolist(), 1000),
        "train_rows": len(train),
        "test_rows": len(test),
        "cost_scenarios": scenarios,
        "conclusion": "A positive gross result is insufficient: higher assumed costs reverse its sign.",
    }
    curve.to_csv(target / "synthetic-equity.csv", index=False)
    with (target / "cost-scenarios.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(scenarios[0]))
        writer.writeheader()
        writer.writerows(scenarios)
    (target / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    body = "\n".join(
        f"| {x['scenario']} | {x['gross_quote']} | {x['fees_quote']} | {x['slippage_quote']} | {x['fx_quote_eur']} | {x['net_eur']} |"
        for x in scenarios
    )
    (target / "REPORT.md").write_text(
        "# Synthetic validation report\n\nNo market performance is represented.\n\n"
        "| Scenario | Gross quote | Fees | Slippage | EUR per quote | Net EUR |\n"
        "|---|---:|---:|---:|---:|---:|\n" + body + "\n\n"
        "Hand check: (100 - 10 - 5) × 0.90 = 76.50 EUR.\n\n"
        "Stress: (100 - 10 - 110) × 0.90 = -18.00 EUR.\n\n"
        "Drawdown: (1100 - 990) / 1100 = 10%. The first loss is also measured against initial capital.\n\n"
        "Chronological split: three observations before 4 January, two from 4 January.\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
