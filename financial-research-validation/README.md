# Financial research platform

Python platform for backtesting, transaction costs, portfolio risk and simulated order reconciliation.

The project explores financial hypotheses and follows their consequences through simulation and accounting. It compares portfolio variants with passive references, records research decisions and keeps order and position records available for inspection.

![Actual dashboard panels showing positions, order states and fills](media/product-overview.png)

**[Dashboard tour →](docs/PRODUCT_TOUR.md)** · [Methodology](docs/METHODOLOGY.md) · [Source provenance](docs/PROVENANCE.md)

## How it works

The wider platform uses Python, pandas, simulation tools and transactional storage. This folder provides two smaller runnable examples: an order lifecycle model and numerical validation. Both run with synthetic demo data.

### An uncertain response is a state to reconcile

The execution demo persists an order identity before submission. A timeout changes it to `UNKNOWN`; it is not submitted again under another identity. Partial fills are recorded once by fill ID. New entries remain blocked while the response is unresolved, the position differs from the ledger or protective stop coverage is unconfirmed.

![Simulated order lifecycle and reconciliation](media/order-lifecycle.svg)

The final reconciliation matches ten units, two fills and a confirmed stop covering the position. A simulated restart requires a fresh reconciliation before opening the entry gate. [The tests](tests/test_execution.py) also cover overfills, duplicate fill conflicts, cancellation races and missing protection.

### Keep the financial conventions explicit

Cost assumptions can reverse a conclusion: `(100 − 10 − 5) × 0.90 = €76.50`, while higher slippage changes it to `−€18.00`. Daily-return checks identify missing observations and use UTC closing boundaries. Partial exits with different entry IDs remain separate even when venue, symbol and entry time match.

![Synthetic cost and drawdown calculations](media/research-overview.png)

[Worked calculations](examples/REPORT.md) explain the figures and conventions. They are software examples rather than market performance.

## Demo

Requires Python **3.12.13** and uv **0.10.9**. From this folder:

```sh
uv sync --frozen
uv run python demo.py
uv run python execution_demo.py
```

The numerical demo writes fixed fixtures and results to `examples/`. The execution demo prints its event history and ends in `FILLED`, with ten units reconciled and €208 entry cost. All order and stop observations are supplied locally; there is no broker connector in the demo.

## Tests

```sh
uv run ruff check .
uv run pytest -q
```

Tests cover entry identity, partial exits, chronological data checks, costs, drawdown, uncertain responses and reconciliation failures. [Methodology](docs/METHODOLOGY.md) also records a research direction that was not promoted. Current strategy rules, parameters and account configuration remain private. Sustainable live profitability and operational acceptance remain unestablished.

## En español

Plataforma personal de investigación, backtesting y control de operaciones. La muestra permite seguir una orden ficticia, revisar ejecuciones parciales y comprobar por qué una entrada queda bloqueada hasta conciliar posiciones y protección. Incluye también cálculos reproducibles de costes y métricas.

[Rights](RIGHTS.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)
