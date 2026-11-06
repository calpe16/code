![Martin Calpe Blasco — Financial research and technology](media/portfolio-banner.svg)

# Martin Calpe Blasco

BSc in Mathematics in Finance and Industry from TU Braunschweig, with experience in financial services at Volkswagen and German-market operations and investment research at Rankia. Based in Valencia, Spain.

My projects connect financial questions with software, from research and portfolio accounting to the management of everyday financial data.

## Quantitative Trading Research Platform

A Python research platform with chronological backtesting, transaction costs, portfolio accounting and simulated order reconciliation. Start with the independent moving-average experiment: seeded data, next-open fills, four cost cases and a passive benchmark.

[![Research dashboard panels with synthetic records](financial-research-validation/media/product-overview.png)](financial-research-validation/README.md)

**[Open the quantitative project →](financial-research-validation/README.md)** · [Generated experiment](financial-research-validation/examples/backtest/REPORT.md)

```sh
cd financial-research-validation
uv sync --frozen
uv run python backtest_demo.py --check
```

Then run `uv run python execution_demo.py` to inspect a timeout, partial fills, reconciliation and local entry gates. The demonstrations use local fixtures after dependencies are installed.

## Brújula

Flutter/Dart application for personal finance, documents and productivity. The runnable modules cover financial-import review and a two-device synchronization conflict, alongside a tour of the original app.

[![Brújula desktop and phone-width screens](brujula-finance-case-study/media/product-overview.png)](brujula-finance-case-study/README.md)

[Explore Brújula →](brujula-finance-case-study/README.md) · [Product tour](brujula-finance-case-study/docs/PRODUCT_TOUR.md)

## Development

These projects were developed with AI-assisted tools. I defined the requirements, reviewed implementations, tested behaviour and iterated on the results. Component provenance is documented within each project.

Demonstrations use synthetic data. Full applications, personal records and current trading strategies remain private. This preparation repository is private; links require access.

[LinkedIn](https://www.linkedin.com/in/martin-calpe-blasco)
